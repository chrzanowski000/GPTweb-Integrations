package com.formulaarchiver

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Create
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.formulaarchiver.settings.SettingsRepository
import com.formulaarchiver.settings.SettingsScreen
import com.formulaarchiver.settings.SettingsViewModel
import com.formulaarchiver.ui.ManualArchiveScreen
import com.formulaarchiver.ui.StatusViewModel

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val repo = SettingsRepository(applicationContext)

        val settingsViewModel = ViewModelProvider(this, object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                SettingsViewModel(repo) as T
        })[SettingsViewModel::class.java]

        val statusViewModel = ViewModelProvider(this, object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                StatusViewModel(repo) as T
        })[StatusViewModel::class.java]

        setContent {
            MaterialTheme {
                var selectedTab by remember { mutableIntStateOf(0) }

                Scaffold(
                    bottomBar = {
                        NavigationBar {
                            NavigationBarItem(
                                selected = selectedTab == 0,
                                onClick = { selectedTab = 0 },
                                icon = { Icon(Icons.Default.Create, contentDescription = null) },
                                label = { Text("Archive") }
                            )
                            NavigationBarItem(
                                selected = selectedTab == 1,
                                onClick = { selectedTab = 1 },
                                icon = { Icon(Icons.Default.Settings, contentDescription = null) },
                                label = { Text("Settings") }
                            )
                        }
                    }
                ) { padding ->
                    when (selectedTab) {
                        0 -> ManualArchiveScreen(
                            viewModel = statusViewModel,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(padding)
                        )
                        1 -> SettingsScreen(
                            viewModel = settingsViewModel,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(padding)
                        )
                    }
                }
            }
        }
    }
}
