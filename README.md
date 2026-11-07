> ⚠️ **本 repo 已搬家，不再更新（2026-11-07）**
>
> 「用得了」參賽作品的城市通 App 已經連同完整 git 歷史，併進 [Peakqi-com/townpass2026-peakqi](https://github.com/Peakqi-com/townpass2026-peakqi) 的 [`townpass/`](https://github.com/Peakqi-com/townpass2026-peakqi/tree/main/townpass) 資料夾；文件在該 repo 的 [`docs/`](https://github.com/Peakqi-com/townpass2026-peakqi/tree/main/docs)。請到那裡開發與提交，不要再 push 到這裡。

# What is Town Pass?

Town Pass is an open-source project developed by the Taipei City Government. With the growth of smart cities, the demand for digitalization in city management and citizen services continues to rise. As we enter a new digital era, our goal is to involve citizens in the process, combining third-party expertise and innovation to make digital life in Taipei more convenient.

Town Pass is not just an application; it is an open community project. Through open-source, every citizen can participate in the ideation, development, and optimization of the application. This not only enhances citizen engagement and satisfaction but also leverages collective intelligence to continuously improve the application, making it truly serve the people. Furthermore, we hope that various municipalities can widely adopt the open-source framework of Town Pass, integrate it with their existing municipal service systems, and quickly have their own applications to enhance digital governance.

Open source is a key driver of technological progress and social development. Through open-source, Town Pass will become an ever-evolving platform, attracting developers from all backgrounds to contribute. We welcome experts to submit code, report issues, provide suggestions, and even develop new features and creative ideas, working together to perfect Town Pass as we advance toward a smart city.

# Getting Started

We highly recommend to read through our [document](https://tpe-guideline.web.app/en/docs/) for more detail.

Here are some quick setup guide.

## Requirement

- [Flutter](https://docs.flutter.dev/get-started/install) or [FVM](https://fvm.app/documentation/getting-started/installation)
- [XCode](https://developer.apple.com/xcode/) (for iOS)
- [Android SDK](https://developer.android.com/studio/index.html) (for Android, with or without Android Studio)

## Build the Project

1. Get the packages project needed:

   ``` bash
   flutter pub get
   ```

2. Generate additional needed dart code for the project.

   ``` bash
   dart run build_runner build
   ```

3. You are all set now, Run the project from your IDE or the through the command line:

   ``` bash
   flutter run
   ```
