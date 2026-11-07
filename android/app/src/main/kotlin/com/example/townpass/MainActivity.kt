package com.example.townpass

import android.os.Build
import android.speech.SpeechRecognizer
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // 長輩模式 listen Handler 用：speech_to_text 在裝置不支援離線辨識時，
        // 會默默改用預設（雲端）辨識器，違反「執行時推論必須在裝置端」的規則。
        // 開始辨識前先用這個方法確認裝置端辨識可用（Android 12 / API 31 起才有）。
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "town_pass/elder_mode")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "isOnDeviceRecognitionAvailable" -> result.success(
                        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                            SpeechRecognizer.isOnDeviceRecognitionAvailable(this)
                    )
                    else -> result.notImplemented()
                }
            }
    }
}
