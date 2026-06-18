package com.formulaarchiver.network

import com.google.gson.annotations.SerializedName

data class Message(
    @SerializedName("role") val role: String,
    @SerializedName("content") val content: String
)

data class ArchiveRequest(
    @SerializedName("chat_title") val chatTitle: String,
    @SerializedName("source") val source: String,
    @SerializedName("messages") val messages: List<Message>
)

data class ArchiveResponse(
    @SerializedName("status") val status: String,
    @SerializedName("formula_name") val formulaName: String,
    @SerializedName("version") val version: String,
    @SerializedName("rows_written") val rowsWritten: Int
)

data class ErrorBody(
    @SerializedName("detail") val detail: String
)
