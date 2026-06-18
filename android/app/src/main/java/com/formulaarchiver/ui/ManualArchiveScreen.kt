package com.formulaarchiver.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun ManualArchiveScreen(viewModel: StatusViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.state.collectAsState()
    var recipeText by remember { mutableStateOf("") }

    val isLoading = state is UiState.Loading

    Column(
        modifier = modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        OutlinedTextField(
            value = recipeText,
            onValueChange = { recipeText = it },
            label = { Text("Paste recipe here") },
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            enabled = !isLoading
        )

        Button(
            onClick = { viewModel.processManual(recipeText) },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading
        ) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                Spacer(modifier = Modifier.width(8.dp))
            }
            Text("Archive Formula")
        }

        OutlinedButton(
            onClick = {
                recipeText = ""
                viewModel.resetState()
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading
        ) {
            Text("Clear")
        }

        when (val s = state) {
            is UiState.Success ->
                ResultCard(
                    title = "Formula Archived",
                    lines = listOf(
                        "Formula:" to s.response.formulaName,
                        "Version:" to s.response.version,
                        "Rows written:" to s.response.rowsWritten.toString()
                    ),
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    onDismiss = { viewModel.resetState() }
                )
            is UiState.Error ->
                ResultCard(
                    title = "Archive Failed",
                    lines = listOf("Error:" to s.message),
                    containerColor = MaterialTheme.colorScheme.errorContainer,
                    onDismiss = { viewModel.resetState() }
                )
            else -> {}
        }
    }
}
