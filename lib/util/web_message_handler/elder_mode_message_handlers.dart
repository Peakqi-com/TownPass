import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:town_pass/util/elder_mode_config.dart';
import 'package:town_pass/util/web_message_handler/tp_web_message_handler.dart';

// 長輩模式新增的 App 能力（規格見 docs/townpass/elder-mode-spec.md M0）。
//
// 每個 Handler 都透過介面取得平台功能（TTS、震動、開啟外部 App、語音辨識），
// 正式實作在 elder_mode_platform.dart；測試時換成假實作。

/// 系統文字轉語音。
abstract interface class ElderModeTts {
  Future<bool> speak(String text, {required double rate});
}

/// 觸覺回饋。
abstract interface class ElderModeHaptics {
  Future<void> light();
  Future<void> medium();
}

/// 交給外部 App 開啟連結（LINE、簡訊、電話、Email）。
abstract interface class ElderModeLauncher {
  Future<bool> openExternal(Uri uri);
}

/// 裝置端語音辨識。實作必須保證音訊不離開手機。
abstract interface class ElderModeSpeechRecognizer {
  /// 這支手機能不能在裝置端辨識 [locale]。回傳 false 時不可以開始辨識。
  Future<bool> isOnDeviceAvailable(String locale);

  Future<void> start({
    required String locale,
    required void Function(String text) onFinal,
    required void Function(String error) onError,
  });

  Future<void> stop();

  Future<void> cancel();
}

typedef A11yStateReader = ({bool screenReader, double textScale}) Function();

/// `speak`：唸出文字。
///
/// 網頁送出 `'叫車'` 或 `{ text: '叫車', rate: 0.45 }`，App 回覆 `true`／`false`。
class SpeakMessageHandler extends TPWebMessageHandler {
  SpeakMessageHandler({required this.tts});

  final ElderModeTts tts;

  static const double defaultRate = 0.45;
  static const double minRate = 0.2;
  /// flutter_tts 允許的最大值。視障者習慣用一般 3～5 倍的速度聆聽，
  /// 所以上限不能照長輩的需求寫死；實際能多快依各平台的 TTS 引擎而定。
  static const double maxRate = 1.0;
  static const int maxLength = 200;

  @override
  String get name => 'speak';

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required onReply,
  }) async {
    final (String? text, double rate) = switch (message) {
      String s => (s, defaultRate),
      {'text': String s, 'rate': num r} => (s, r.toDouble().clamp(minRate, maxRate)),
      {'text': String s} => (s, defaultRate),
      _ => (null, defaultRate),
    };

    if (text == null || text.trim().isEmpty || text.length > maxLength) {
      onReply?.call(replyWebMessage(data: false));
      return;
    }

    final bool ok = await tts.speak(text.trim(), rate: rate);
    onReply?.call(replyWebMessage(data: ok));
  }
}

/// `a11y_state`：回覆 `{ screenReader, textScale }`。
///
/// 網頁用 `screenReader` 決定要不要自己唸（避免和 VoiceOver／TalkBack 重複），
/// 用 `textScale` 設定根字級（iOS WebView 不會跟隨系統字級）。
class A11yStateMessageHandler extends TPWebMessageHandler {
  A11yStateMessageHandler({required this.read});

  final A11yStateReader read;

  @override
  String get name => 'a11y_state';

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required onReply,
  }) async {
    final state = read();
    onReply?.call(replyWebMessage(data: {
      'screenReader': state.screenReader,
      'textScale': state.textScale,
    }));
  }
}

/// `haptic`：`'medium'` 中等震動，其他一律輕震動。iOS WebView 不支援
/// `navigator.vibrate`，所以統一由 App 處理。
class HapticMessageHandler extends TPWebMessageHandler {
  HapticMessageHandler({required this.haptics});

  final ElderModeHaptics haptics;

  @override
  String get name => 'haptic';

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required onReply,
  }) async {
    if (message == 'medium') {
      await haptics.medium();
    } else {
      await haptics.light();
    }
    onReply?.call(replyWebMessage(data: true));
  }
}

/// `open_external`：用外部 App 開啟連結，回覆 `true`／`false`。
///
/// 內建的 `launch_map` 會先用 `canLaunchUrl` 檢查，而且用預設開啟模式，
/// LINE 連結不一定會跳到 LINE App；這裡固定交給外部 App。
/// 只允許 https、tel、sms、mailto，避免網頁開啟 javascript、file、intent 等連結。
class OpenExternalMessageHandler extends TPWebMessageHandler {
  OpenExternalMessageHandler({required this.launcher});

  final ElderModeLauncher launcher;

  static const Set<String> allowedSchemes = {'https', 'tel', 'sms', 'mailto'};

  @override
  String get name => 'open_external';

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required onReply,
  }) async {
    final Uri? uri = message is String ? Uri.tryParse(message) : null;
    if (uri == null || !allowedSchemes.contains(uri.scheme)) {
      onReply?.call(replyWebMessage(data: false));
      return;
    }

    final bool ok = await launcher.openExternal(uri);
    onReply?.call(replyWebMessage(data: ok));
  }
}

/// `listen`：裝置端語音辨識。
///
/// 網頁送出 `{ action: 'start' | 'stop' | 'cancel', locale?: 'zh-TW' }`。
/// `start` 會先回覆 `{ status: 'listening' }`，辨識完成再回覆 `{ text }`，
/// 失敗回覆 `{ error }`。
///
/// 兩道把關：
/// 1. 只有長輩模式的網域可以使用（麥克風屬於隱私）。
/// 2. 裝置不支援離線辨識時直接回覆 `offline_unavailable`，絕不開始辨識，
///    因為競賽規則規定執行時的推論必須在裝置端完成。
class ListenMessageHandler extends TPWebMessageHandler {
  ListenMessageHandler({required this.recognizer});

  final ElderModeSpeechRecognizer recognizer;

  static const String defaultLocale = 'zh-TW';

  @override
  String get name => 'listen';

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required onReply,
  }) async {
    void reply(Map<String, String> data) => onReply?.call(replyWebMessage(data: data));

    if (!ElderModeConfig.isTrustedOrigin(sourceOrigin)) {
      reply({'error': 'forbidden'});
      return;
    }

    final Object? action = message is Map ? message['action'] : null;
    switch (action) {
      case 'start':
        final Object? requested = (message as Map)['locale'];
        final String locale = requested is String && requested.isNotEmpty ? requested : defaultLocale;
        if (!await recognizer.isOnDeviceAvailable(locale)) {
          reply({'error': 'offline_unavailable'});
          return;
        }
        await recognizer.start(
          locale: locale,
          onFinal: (text) => reply({'text': text}),
          onError: (error) => reply({'error': error}),
        );
        reply({'status': 'listening'});
      case 'stop':
        await recognizer.stop();
        reply({'status': 'stopped'});
      case 'cancel':
        await recognizer.cancel();
        reply({'status': 'cancelled'});
      default:
        reply({'error': 'bad_request'});
    }
  }
}
