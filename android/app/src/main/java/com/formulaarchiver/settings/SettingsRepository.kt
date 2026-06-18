package com.formulaarchiver.settings

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

data class AppSettings(
    val backendUrl: String,
    val triggerPhrase: String
)

class SettingsRepository(private val context: Context) {

    companion object {
        private val KEY_BACKEND_URL = stringPreferencesKey("backend_url")
        private val KEY_TRIGGER_PHRASE = stringPreferencesKey("trigger_phrase")

        const val DEFAULT_BACKEND_URL = "http://192.168.1.100:8000"
        const val DEFAULT_TRIGGER_PHRASE = "#SAVE_FORMULA"
    }

    val settingsFlow: Flow<AppSettings> = context.dataStore.data.map { prefs ->
        AppSettings(
            backendUrl = prefs[KEY_BACKEND_URL] ?: DEFAULT_BACKEND_URL,
            triggerPhrase = prefs[KEY_TRIGGER_PHRASE] ?: DEFAULT_TRIGGER_PHRASE
        )
    }

    suspend fun saveSettings(backendUrl: String, triggerPhrase: String) {
        context.dataStore.edit { prefs ->
            prefs[KEY_BACKEND_URL] = backendUrl.trim()
            prefs[KEY_TRIGGER_PHRASE] = triggerPhrase.trim()
        }
    }
}
