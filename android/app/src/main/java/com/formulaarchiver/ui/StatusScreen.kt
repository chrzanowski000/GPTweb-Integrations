package com.formulaarchiver.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.formulaarchiver.network.ApiClient
import com.formulaarchiver.network.ArchiveRequest
import com.formulaarchiver.network.ArchiveResponse
import com.formulaarchiver.network.ErrorBody
import com.formulaarchiver.network.Message
import com.formulaarchiver.settings.SettingsRepository
import com.formulaarchiver.util.TriggerValidator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

sealed class UiState {
    object Idle : UiState()
    object Loading : UiState()
    object KeywordNotFound : UiState()
    data class Success(val response: ArchiveResponse) : UiState()
    data class Error(val message: String) : UiState()
}

class StatusViewModel(private val repo: SettingsRepository) : ViewModel() {
    private val _state = MutableStateFlow<UiState>(UiState.Idle)
    val state: StateFlow<UiState> = _state

    fun process(sharedText: String) {
        viewModelScope.launch {
            _state.value = UiState.Loading
            val settings = repo.settingsFlow.first()

            if (!TriggerValidator.contains(sharedText, settings.triggerPhrase)) {
                _state.value = UiState.KeywordNotFound
                return@launch
            }

            val request = ArchiveRequest(
                chatTitle = "Shared from Android",
                source = "android_share",
                messages = listOf(Message(role = "user", content = sharedText))
            )

            try {
                val api = ApiClient.getApi(settings.backendUrl)
                val response = api.archive(request)
                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null) {
                        _state.value = UiState.Success(body)
                    } else {
                        _state.value = UiState.Error("Empty response from backend")
                    }
                } else {
                    val errorJson = response.errorBody()?.string() ?: ""
                    val detail = runCatching {
                        ApiClient.gson.fromJson(errorJson, ErrorBody::class.java).detail
                    }.getOrElse { "HTTP ${response.code()}" }
                    _state.value = UiState.Error(detail)
                }
            } catch (e: Exception) {
                _state.value = UiState.Error(e.message ?: "Network error")
            }
        }
    }
}

@Composable
fun StatusScreen(
    viewModel: StatusViewModel,
    sharedText: String,
    onDismiss: () -> Unit
) {
    val state by viewModel.state.collectAsState()

    LaunchedEffect(sharedText) {
        viewModel.process(sharedText)
    }

    MaterialTheme {
        Surface(modifier = Modifier.fillMaxWidth()) {
            when (val s = state) {
                is UiState.Idle, is UiState.Loading ->
                    LoadingIndicator(message = "Archiving formula…")

                is UiState.KeywordNotFound ->
                    ResultCard(
                        title = "Keyword Not Found",
                        lines = listOf("" to "The shared text does not contain the trigger phrase."),
                        containerColor = MaterialTheme.colorScheme.errorContainer,
                        onDismiss = onDismiss
                    )

                is UiState.Success ->
                    ResultCard(
                        title = "Formula Archived",
                        lines = listOf(
                            "Formula:" to s.response.formulaName,
                            "Version:" to s.response.version,
                            "Rows written:" to s.response.rowsWritten.toString()
                        ),
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        onDismiss = onDismiss
                    )

                is UiState.Error ->
                    ResultCard(
                        title = "Archive Failed",
                        lines = listOf("Error:" to s.message),
                        containerColor = MaterialTheme.colorScheme.errorContainer,
                        onDismiss = onDismiss
                    )
            }
        }
    }
}
