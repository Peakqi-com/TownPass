import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:town_pass/util/elder_mode_config.dart';

void main() {
  group('isTrustedOrigin', () {
    test('長輩模式的 https 網域是可信任的', () {
      expect(ElderModeConfig.isTrustedOrigin(WebUri('https://townpass2026-peakqi.vercel.app')), isTrue);
    });

    test('其他網域、http、null 都不可信任', () {
      expect(ElderModeConfig.isTrustedOrigin(WebUri('https://evil.example.com')), isFalse);
      expect(ElderModeConfig.isTrustedOrigin(WebUri('http://townpass2026-peakqi.vercel.app')), isFalse);
      expect(ElderModeConfig.isTrustedOrigin(WebUri('https://townpass2026-peakqi.vercel.app.evil.com')), isFalse);
      expect(ElderModeConfig.isTrustedOrigin(null), isFalse);
    });
  });
}
