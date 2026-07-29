plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
    id("com.google.gms.google-services")
}

android {
    namespace = "com.turion.turion_ai_trader"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.turion.turion_ai_trader"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        // Updated: 2026-07-29 - a fixed, committed debug keystore (standard
        // Android debug credentials - not a secret, this app is debug-signed
        // only, never published to a store). Without this, Gradle's default
        // "debug" signingConfig auto-generates a fresh keystore per machine/
        // CI runner, so every GitHub Actions build was signed differently
        // and `adb install -r` against the previous build kept failing with
        // INSTALL_FAILED_UPDATE_INCOMPATIBLE - hit 3 times before this fix.
        create("sharedDebug") {
            storeFile = file("debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the shared debug key for now, so `flutter run
            // --release` and repeated CI builds both work and stay
            // install-compatible with each other.
            signingConfig = signingConfigs.getByName("sharedDebug")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
