import 'package:flutter_inappwebview/flutter_inappwebview.dart';

/// 長輩模式微服務的設定。
///
/// 長輩模式需要一些其他微服務不需要的能力（例如麥克風），
/// 這些能力只開放給下面列出的網域，避免影響或暴露給其他微服務。
abstract final class ElderModeConfig {
  /// 長輩模式網頁的網域。新增部署網址（例如預覽網址、ngrok）時加在這裡。
  static const Set<String> trustedHosts = {
    'townpass2026-peakqi.vercel.app',
  };

  /// 只接受 https 且網域完全相符的來源。
  static bool isTrustedOrigin(WebUri? origin) {
    if (origin == null) return false;
    return origin.scheme == 'https' && trustedHosts.contains(origin.host);
  }
}
