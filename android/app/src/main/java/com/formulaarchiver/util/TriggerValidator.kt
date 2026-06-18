package com.formulaarchiver.util

object TriggerValidator {
    fun contains(text: String, trigger: String): Boolean =
        trigger.isNotBlank() && text.contains(trigger.trim(), ignoreCase = true)
}
