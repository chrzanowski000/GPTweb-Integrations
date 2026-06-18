package com.formulaarchiver.network

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface BackendApi {
    @GET("health")
    suspend fun health(): Response<Map<String, Boolean>>

    @POST("archive")
    suspend fun archive(@Body request: ArchiveRequest): Response<ArchiveResponse>
}
