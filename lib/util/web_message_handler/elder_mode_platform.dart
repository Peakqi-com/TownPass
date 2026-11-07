import 'dart:io' show Platform;

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:town_pass/util/web_message_handler/elder_mode_message_handlers.dart';
import 'package:url_launcher/url_launcher.dart';

// elder_mode_message_handlers.dart 介面的正式實作，直接呼叫套件。
// 這一層刻意保持很薄，邏輯（驗證、把關）都在 Handler 裡，由單元測試涵蓋。

/// 用 flutter_tts 呼叫系統 TTS（離線需要手機已安裝中文語音包）。
class FlutterTtsAdapter implements ElderModeTts {
  final FlutterTts _tts = FlutterTts();
  bool _configured = false;

  @override
  Future<bool> speak(String text, {required double rate}) async {
    try {
      if (!_configured) {
        await _tts.setLanguage('zh-TW');
        _configured = true;
      }
      // 長輩連續點按時，只唸最後一個，不排隊。
      await _tts.stop();
      await _tts.setSpeechRate(rate);
      return await _tts.speak(text) == 1;
    } catch (_) {
      return false;
    }
  }
}

class SystemHaptics implements ElderModeHaptics {
  @override
  Future<void> light() => HapticFeedback.lightImpact();

  @override
  Future<void> medium() => HapticFeedback.mediumImpact();
}

class ExternalAppLauncher implements ElderModeLauncher {
  @override
  Future<bool> openExternal(Uri uri) async {
    try {
      return await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      return false;
    }
  }
}

/// 用 speech_to_text 做裝置端辨識。
///
/// iOS：套件在 `onDevice: true` 時會設定 `requiresOnDeviceRecognition`，
/// 不支援就直接失敗，不會上雲。
/// Android：套件在裝置不支援時會**默默改用預設（雲端）辨識器**，
/// 所以先透過 MainActivity 的原生方法確認 `isOnDeviceRecognitionAvailable`。
class SpeechToTextRecognizer implements ElderModeSpeechRecognizer {
  static const MethodChannel _channel = MethodChannel('town_pass/elder_mode');

  final SpeechToText _speech = SpeechToText();
  bool? _initialized;
  void Function(String text)? _onFinal;
  void Function(String error)? _onError;

  Future<bool> _ensureInitialized() async {
    return _initialized ??= await _speech.initialize(
      onError: (SpeechRecognitionError error) => _onError?.call(error.errorMsg),
    );
  }

  @override
  Future<bool> isOnDeviceAvailable(String locale) async {
    if (Platform.isIOS) return true;
    try {
      return await _channel.invokeMethod<bool>('isOnDeviceRecognitionAvailable') ?? false;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<void> start({
    required String locale,
    required void Function(String text) onFinal,
    required void Function(String error) onError,
  }) async {
    _onFinal = onFinal;
    _onError = onError;
    if (!await _ensureInitialized()) {
      onError('permission_denied');
      return;
    }
    await _speech.listen(
      onResult: (SpeechRecognitionResult result) {
        if (result.finalResult) _onFinal?.call(result.recognizedWords);
      },
      listenOptions: SpeechListenOptions(
        onDevice: true,
        partialResults: false,
        cancelOnError: true,
        listenMode: ListenMode.confirmation,
        localeId: locale.replaceAll('-', '_'),
      ),
    );
  }

  @override
  Future<void> stop() => _speech.stop();

  @override
  Future<void> cancel() => _speech.cancel();
}

/// 用 App 已有的 flutter_local_notifications 排程本機通知（App 關掉也會跳出來）。
///
/// 時間一律換成 UTC 排程，不需要載入時區資料庫，也不受手機時區設定影響。
/// Android 用 inexact 模式：不需要「精確鬧鐘」權限，可能晚幾分鐘，對提醒申請截止日已經足夠。
/// 通知頻道沿用 NotificationService 的設定。
class LocalNotificationReminders implements ElderModeReminders {
  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();

  Future<bool> _ensurePermission() async {
    if (Platform.isAndroid) {
      final android = _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
      return await android?.requestNotificationsPermission() ?? true;
    }
    if (Platform.isIOS) {
      final ios = _plugin.resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>();
      return await ios?.requestPermissions(alert: true, badge: true, sound: true) ?? false;
    }
    return false;
  }

  @override
  Future<bool> schedule({required int id, required String title, required String body, required DateTime at}) async {
    try {
      if (!await _ensurePermission()) return false;
      await _plugin.zonedSchedule(
        id: id,
        title: title,
        body: body,
        scheduledDate: tz.TZDateTime.from(at.toUtc(), tz.UTC),
        notificationDetails: const NotificationDetails(
          android: AndroidNotificationDetails(
            'TownPass android notification id',
            'TownPass android notification channel name',
            importance: Importance.max,
            priority: Priority.max,
          ),
          iOS: DarwinNotificationDetails(),
        ),
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<void> cancel(int id) async {
    try {
      await _plugin.cancel(id: id);
    } catch (_) {
      // 已經不存在的提醒，取消失敗也沒關係
    }
  }
}

/// 讀取系統的無障礙狀態；不需要 BuildContext。
({bool screenReader, double textScale}) readSystemA11yState() {
  final dispatcher = WidgetsBinding.instance.platformDispatcher;
  return (
    screenReader: dispatcher.accessibilityFeatures.accessibleNavigation,
    textScale: dispatcher.textScaleFactor,
  );
}
