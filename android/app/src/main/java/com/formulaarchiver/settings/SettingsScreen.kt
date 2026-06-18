package com.formulaarchiver.settings

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.formulaarchiver.network.ApiClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

sealed class ConnectionState {
    object Idle : ConnectionState()
    object Testing : ConnectionState()
    object Connected : ConnectionState()
    data class Failed(val reason: String) : ConnectionState()
}

class SettingsViewModel(private val repo: SettingsRepository) : ViewModel() {
    private val _settings = MutableStateFlow(
        AppSettings(
            backendUrl = SettingsRepository.DEFAULT_BACKEND_URL,
            triggerPhrase = SettingsRepository.DEFAULT_TRIGGER_PHRASE
        )
    )
    val settings: StateFlow<AppSettings> = _settings

    private val _saved = MutableStateFlow(false)
    val saved: StateFlow<Boolean> = _saved

    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Idle)
    val connectionState: StateFlow<ConnectionState> = _connectionState

    init {
        viewModelScope.launch {
            _settings.value = repo.settingsFlow.first()
        }
    }

    fun save(backendUrl: String, triggerPhrase: String) {
        viewModelScope.launch {
            repo.saveSettings(backendUrl, triggerPhrase)
            _settings.value = AppSettings(backendUrl, triggerPhrase)
            _saved.value = true
        }
    }

    fun clearSaved() {
        _saved.value = false
    }

    fun testConnection(backendUrl: String) {
        viewModelScope.launch {
            _connectionState.value = ConnectionState.Testing
            try {
                val api = ApiClient.getApi(backendUrl)
                val response = api.health()
                if (response.isSuccessful) {
                    _connectionState.value = ConnectionState.Connected
                } else {
                    _connectionState.value = ConnectionState.Failed("HTTP ${response.code()}")
                }
            } catch (e: Exception) {
                _connectionState.value = ConnectionState.Failed(e.message ?: "Unreachable")
            }
        }
    }

    fun clearConnectionState() {
        _connectionState.value = ConnectionState.Idle
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(viewModel: SettingsViewModel) {
    val settings by viewModel.settings.collectAsState()
    val saved by viewModel.saved.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()

    var urlField by remember(settings.backendUrl) { mutableStateOf(settings.backendUrl) }
    var triggerField by remember(settings.triggerPhrase) { mutableStateOf(settings.triggerPhrase) }

    if (saved) {
        LaunchedEffect(Unit) {
            kotlinx.coroutines.delay(1500)
            viewModel.clearSaved()
        }
    }

    if (connectionState is ConnectionState.Connected || connectionState is ConnectionState.Failed) {
        LaunchedEffect(connectionState) {
            kotlinx.coroutines.delay(3000)
            viewModel.clearConnectionState()
        }
    }

    MaterialTheme {
        Scaffold(
            topBar = { TopAppBar(title = { Text("Settings") }) }
        ) { padding ->
            Column(
                modifier = Modifier
                    .padding(padding)
                    .padding(16.dp)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                OutlinedTextField(
                    value = urlField,
                    onValueChange = { urlField = it },
                    label = { Text("Backend URL") },
                    placeholder = { Text("http://192.168.x.x:8000") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                OutlinedTextField(
                    value = triggerField,
                    onValueChange = { triggerField = it },
                    label = { Text("Trigger Phrase") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Button(
                    onClick = { viewModel.save(urlField, triggerField) },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Save Settings")
                }
                OutlinedButton(
                    onClick = { viewModel.testConnection(urlField) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = connectionState !is ConnectionState.Testing
                ) {
                    if (connectionState is ConnectionState.Testing) {
                        CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                        Spacer(modifier = Modifier.width(8.dp))
                    }
                    Text("Test Connection")
                }

                when (val cs = connectionState) {
                    is ConnectionState.Connected ->
                        Text(
                            text = "Backend Connected",
                            color = MaterialTheme.colorScheme.primary,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    is ConnectionState.Failed ->
                        Text(
                            text = "Cannot Reach Backend: ${cs.reason}",
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    else -> {}
                }

                if (saved) {
                    Text(
                        text = "Settings saved.",
                        color = MaterialTheme.colorScheme.primary,
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }
        }
    }
}
