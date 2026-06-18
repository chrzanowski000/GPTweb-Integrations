package com.formulaarchiver

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.formulaarchiver.settings.SettingsRepository
import com.formulaarchiver.ui.StatusScreen
import com.formulaarchiver.ui.StatusViewModel

class ShareReceiverActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val repo = SettingsRepository(applicationContext)
        val viewModel = ViewModelProvider(this, object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                StatusViewModel(repo) as T
        })[StatusViewModel::class.java]

        val sharedText: String = when {
            intent?.action == Intent.ACTION_SEND && intent.type == "text/plain" ->
                intent.getStringExtra(Intent.EXTRA_TEXT) ?: ""
            else -> ""
        }

        setContent {
            StatusScreen(
                viewModel = viewModel,
                sharedText = sharedText,
                onDismiss = { finish() }
            )
        }
    }
}
