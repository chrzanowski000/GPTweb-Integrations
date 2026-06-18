# Keep Retrofit interfaces and their annotations
-keep,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}
# Keep Gson model classes used for JSON serialization
-keepclassmembers class com.formulaarchiver.network.** {
    <fields>;
}
# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
