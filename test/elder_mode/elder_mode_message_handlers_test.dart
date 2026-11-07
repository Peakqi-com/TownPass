import 'dart:convert';

import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:town_pass/util/web_message_handler/elder_mode_message_handlers.dart';
import 'package:town_pass/util/web_message_handler/tp_web_message_handler.dart';

const _trustedOrigin = 'https://townpass2026-peakqi.vercel.app';
const _otherOrigin = 'https://evil.example.com';

/// 呼叫 Handler，回傳 App 回覆給網頁的每一則 `data`（依序）。
Future<List<Object?>> _invoke(
  TPWebMessageHandler handler,
  Object? message, {
  String? origin = _trustedOrigin,
}) async {
  final replies = <Object?>[];
  await handler.handle(
    message: message,
    sourceOrigin: origin == null ? null : WebUri(origin),
    isMainFrame: true,
    onReply: (reply) {
      final Map decoded = jsonDecode(reply.data as String);
      expect(decoded['name'], handler.name);
      replies.add(decoded['data']);
    },
  );
  return replies;
}

class _FakeTts implements ElderModeTts {
  final spoken = <(String, double)>[];
  bool result = true;

  @override
  Future<bool> speak(String text, {required double rate}) async {
    spoken.add((text, rate));
    return result;
  }
}

class _FakeHaptics implements ElderModeHaptics {
  final calls = <String>[];

  @override
  Future<void> light() async => calls.add('light');

  @override
  Future<void> medium() async => calls.add('medium');
}

class _FakeLauncher implements ElderModeLauncher {
  final opened = <Uri>[];
  bool result = true;

  @override
  Future<bool> openExternal(Uri uri) async {
    opened.add(uri);
    return result;
  }
}

class _FakeRecognizer implements ElderModeSpeechRecognizer {
  bool onDeviceAvailable = true;
  final calls = <String>[];
  void Function(String text)? onFinal;
  void Function(String error)? onError;
  String? startedLocale;

  @override
  Future<bool> isOnDeviceAvailable(String locale) async => onDeviceAvailable;

  @override
  Future<void> start({
    required String locale,
    required void Function(String text) onFinal,
    required void Function(String error) onError,
  }) async {
    calls.add('start');
    startedLocale = locale;
    this.onFinal = onFinal;
    this.onError = onError;
  }

  @override
  Future<void> stop() async => calls.add('stop');

  @override
  Future<void> cancel() async => calls.add('cancel');
}

void main() {
  group('speak', () {
    test('唸出純文字並回覆 true，語速預設 0.45（長輩用較慢語速）', () async {
      final tts = _FakeTts();
      final replies = await _invoke(SpeakMessageHandler(tts: tts), '叫車');

      expect(tts.spoken, [('叫車', 0.45)]);
      expect(replies, [true]);
    });

    test('接受 {text, rate}，語速限制在 0.2～0.7', () async {
      final tts = _FakeTts();
      final handler = SpeakMessageHandler(tts: tts);

      await _invoke(handler, {'text': '看醫生', 'rate': 0.6});
      await _invoke(handler, {'text': '太快', 'rate': 5});
      await _invoke(handler, {'text': '太慢', 'rate': 0});

      expect(tts.spoken, [('看醫生', 0.6), ('太快', 0.7), ('太慢', 0.2)]);
    });

    test('空字串、空白或格式錯誤時回覆 false，而且不唸', () async {
      final tts = _FakeTts();
      final handler = SpeakMessageHandler(tts: tts);

      for (final bad in [null, '', '   ', 42, {'rate': 0.5}, ['叫車']]) {
        expect(await _invoke(handler, bad), [false], reason: '輸入：$bad');
      }
      expect(tts.spoken, isEmpty);
    });

    test('文字超過 200 字時回覆 false（避免網頁塞入長文）', () async {
      final tts = _FakeTts();
      final replies = await _invoke(SpeakMessageHandler(tts: tts), '字' * 201);

      expect(replies, [false]);
      expect(tts.spoken, isEmpty);
    });

    test('系統 TTS 失敗時回覆 false', () async {
      final tts = _FakeTts()..result = false;
      expect(await _invoke(SpeakMessageHandler(tts: tts), '叫車'), [false]);
    });
  });

  group('a11y_state', () {
    test('回覆螢幕閱讀器狀態與系統字級倍率', () async {
      final handler = A11yStateMessageHandler(
        read: () => (screenReader: true, textScale: 1.3),
      );

      expect(await _invoke(handler, null), [
        {'screenReader': true, 'textScale': 1.3},
      ]);
    });
  });

  group('haptic', () {
    test("'medium' 用中等震動，其他一律輕震動，並回覆 true", () async {
      final haptics = _FakeHaptics();
      final handler = HapticMessageHandler(haptics: haptics);

      expect(await _invoke(handler, 'medium'), [true]);
      expect(await _invoke(handler, 'light'), [true]);
      expect(await _invoke(handler, null), [true]);

      expect(haptics.calls, ['medium', 'light', 'light']);
    });
  });

  group('open_external', () {
    test('允許 https、tel、sms、mailto，交給外部 App 開啟並回覆結果', () async {
      final launcher = _FakeLauncher();
      final handler = OpenExternalMessageHandler(launcher: launcher);

      for (final url in [
        'https://line.me/R/ti/p/@taipeicity1999',
        'tel:1966',
        'sms:0911511902?body=test',
        'mailto:cnad002@gmail.com',
      ]) {
        expect(await _invoke(handler, url), [true], reason: url);
      }
      expect(launcher.opened.map((u) => u.scheme), ['https', 'tel', 'sms', 'mailto']);
    });

    test('拒絕 http、javascript、file、intent 等其他 scheme，不開啟', () async {
      final launcher = _FakeLauncher();
      final handler = OpenExternalMessageHandler(launcher: launcher);

      for (final url in [
        'http://example.com',
        'javascript:alert(1)',
        'file:///etc/passwd',
        'intent://scan/#Intent;scheme=zxing;end',
      ]) {
        expect(await _invoke(handler, url), [false], reason: url);
      }
      expect(launcher.opened, isEmpty);
    });

    test('null、非字串或無法解析時回覆 false，不丟例外', () async {
      final launcher = _FakeLauncher();
      final handler = OpenExternalMessageHandler(launcher: launcher);

      for (final bad in [null, 42, '', 'https://[bad']) {
        expect(await _invoke(handler, bad), [false], reason: '輸入：$bad');
      }
      expect(launcher.opened, isEmpty);
    });

    test('外部 App 開不了時回覆 false', () async {
      final launcher = _FakeLauncher()..result = false;
      final handler = OpenExternalMessageHandler(launcher: launcher);

      expect(await _invoke(handler, 'tel:1966'), [false]);
    });
  });

  group('listen', () {
    test('只接受長輩模式網域；其他網頁不能開麥克風', () async {
      final recognizer = _FakeRecognizer();
      final handler = ListenMessageHandler(recognizer: recognizer);

      final replies = await _invoke(handler, {'action': 'start'}, origin: _otherOrigin);
      final noOrigin = await _invoke(handler, {'action': 'start'}, origin: null);

      expect(replies, [
        {'error': 'forbidden'},
      ]);
      expect(noOrigin, [
        {'error': 'forbidden'},
      ]);
      expect(recognizer.calls, isEmpty);
    });

    test('裝置不支援離線辨識時回覆錯誤，絕不開始辨識（不可退回雲端）', () async {
      final recognizer = _FakeRecognizer()..onDeviceAvailable = false;
      final handler = ListenMessageHandler(recognizer: recognizer);

      final replies = await _invoke(handler, {'action': 'start'});

      expect(replies, [
        {'error': 'offline_unavailable'},
      ]);
      expect(recognizer.calls, isEmpty);
    });

    test('start：預設 zh-TW，先回覆 listening，辨識完成後回覆文字', () async {
      final recognizer = _FakeRecognizer();
      final handler = ListenMessageHandler(recognizer: recognizer);
      final replies = <Object?>[];

      await handler.handle(
        message: {'action': 'start'},
        sourceOrigin: WebUri(_trustedOrigin),
        isMainFrame: true,
        onReply: (reply) => replies.add((jsonDecode(reply.data as String) as Map)['data']),
      );
      recognizer.onFinal!('我要叫車');

      expect(recognizer.startedLocale, 'zh-TW');
      expect(replies, [
        {'status': 'listening'},
        {'text': '我要叫車'},
      ]);
    });

    test('辨識失敗時回覆錯誤代碼', () async {
      final recognizer = _FakeRecognizer();
      final handler = ListenMessageHandler(recognizer: recognizer);
      final replies = <Object?>[];

      await handler.handle(
        message: {'action': 'start'},
        sourceOrigin: WebUri(_trustedOrigin),
        isMainFrame: true,
        onReply: (reply) => replies.add((jsonDecode(reply.data as String) as Map)['data']),
      );
      recognizer.onError!('error_no_match');

      expect(replies.last, {'error': 'error_no_match'});
    });

    test('stop 和 cancel 交給辨識器處理', () async {
      final recognizer = _FakeRecognizer();
      final handler = ListenMessageHandler(recognizer: recognizer);

      expect(await _invoke(handler, {'action': 'stop'}), [
        {'status': 'stopped'},
      ]);
      expect(await _invoke(handler, {'action': 'cancel'}), [
        {'status': 'cancelled'},
      ]);
      expect(recognizer.calls, ['stop', 'cancel']);
    });

    test('未知的 action 回覆錯誤', () async {
      final handler = ListenMessageHandler(recognizer: _FakeRecognizer());

      expect(await _invoke(handler, {'action': 'dance'}), [
        {'error': 'bad_request'},
      ]);
      expect(await _invoke(handler, null), [
        {'error': 'bad_request'},
      ]);
    });
  });
}
