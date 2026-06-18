package com.formulaarchiver.network

import com.google.gson.Gson
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    private var currentBaseUrl: String = ""
    private var _api: BackendApi? = null
    val gson = Gson()

    private fun buildClient(): OkHttpClient =
        OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(
                HttpLoggingInterceptor().apply {
                    level = HttpLoggingInterceptor.Level.BODY
                }
            )
            .build()

    fun getApi(baseUrl: String): BackendApi {
        val normalizedUrl = baseUrl.trimEnd('/') + "/"
        if (_api == null || normalizedUrl != currentBaseUrl) {
            currentBaseUrl = normalizedUrl
            _api = Retrofit.Builder()
                .baseUrl(normalizedUrl)
                .client(buildClient())
                .addConverterFactory(GsonConverterFactory.create(gson))
                .build()
                .create(BackendApi::class.java)
        }
        return _api!!
    }
}
