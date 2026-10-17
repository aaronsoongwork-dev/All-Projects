package com.fit2081.aaron_34076832.nutritrack.genAI

import android.app.Application
import androidx.compose.runtime.mutableStateListOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.fit2081.aaron_34076832.nutritrack.BuildConfig
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntake
import com.google.ai.client.generativeai.GenerativeModel
import com.google.ai.client.generativeai.type.content
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlin.reflect.full.memberProperties

class GenAIViewModel(application: Application) : AndroidViewModel(application) {

    private val _insights = mutableStateListOf<Pair<String, String>>()
    val insights: List<Pair<String, String>> get() = _insights

    private val _uiState: MutableStateFlow<UiState> = MutableStateFlow(UiState.Initial)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    private val generativeModel = GenerativeModel(
        modelName = "gemini-2.5-flash",
        apiKey = BuildConfig.apiKeySafe
    )

    private var clickCount: Int = 0

    fun generateInsights(customPrompt: String, foodIntakeList: List<FoodIntake>) {
        _uiState.value = UiState.Loading
        clickCount++
        val insightsToGenerate = if (clickCount == 1) 3 else 1

        viewModelScope.launch(Dispatchers.IO) {
            try {
                val insightsGeneratedInThisCall = mutableListOf<Pair<String, String>>()

                repeat(insightsToGenerate) {
                    val promptBuilder = StringBuilder()

                    if (customPrompt.isNotBlank()) {
                        promptBuilder.appendLine(customPrompt.trim())
                        promptBuilder.appendLine()
                    }

                    if (_insights.isNotEmpty() || insightsGeneratedInThisCall.isNotEmpty()) {
                        promptBuilder.appendLine("Here are insights that have already been generated (either previously or in this current batch). DO NOT generate insights that are similar in topic, pattern, or specific observation to any of these:")
                        _insights.forEachIndexed { index, (title, content) ->
                            promptBuilder.appendLine("Previous Global Insight ${index + 1}: Title: \"$title\", Content: \"$content\"")
                        }
                        insightsGeneratedInThisCall.forEachIndexed { index, (title, content) ->
                            promptBuilder.appendLine("Previous Batch Insight ${index + 1}: Title: \"$title\", Content: \"$content\"")
                        }
                        promptBuilder.appendLine()
                    }

                    if (foodIntakeList.isNotEmpty()) {
                        promptBuilder.appendLine("Here is a list of patients' dietary intake data for analysis:")
                        foodIntakeList.forEachIndexed { index, foodIntake ->
                            promptBuilder.appendLine("Patient #$index:")
                            FoodIntake::class.memberProperties.forEach { prop ->
                                val value = prop.get(foodIntake)
                                promptBuilder.appendLine("  ${prop.name}: $value")
                            }
                            promptBuilder.appendLine()
                        }
                        promptBuilder.appendLine("Based on the data, generate ONLY ONE useful health or dietary insight. The insight should identify a pattern, trend, or significant observation. Format your entire response STRICTLY as \"Title || Content\". The Title should be concise and without brackets. The Content should be a detailed explanation of the insight. Do NOT include any additional text, concluding remarks, or other insights beyond this single \"Title || Content\" string. Refer to the previous examples for the *kind of content* (e.g., insights about specific food groups, gender differences, dietary variety) that should be generated. If generating multiple insights, ensure variety in topic and focus for each. Consider different aspects like specific food groups, gender differences, consumption patterns, correlations between scores, and general dietary trends.")
                    } else if (customPrompt.isBlank()) {
                        _uiState.value = UiState.Error("No data or prompt provided to generate insights.")
                        return@launch
                    }

                    val response = generativeModel.generateContent(
                        content {
                            text(promptBuilder.toString())
                        }
                    )
                    response.text?.let { outputText ->
                        val parts = outputText.split("||")
                        val title = parts.getOrNull(0)?.trim()?.replace("[", "")?.replace("]", "") ?: "Insight"
                        val content = parts.getOrNull(1)?.trim() ?: outputText.trim()
                        val newInsight = title to content
                        _insights.add(newInsight)
                        insightsGeneratedInThisCall.add(newInsight)
                    }
                }
                _uiState.value = UiState.Success("")
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.localizedMessage ?: "Unknown error occurred during insight generation.")
            }
        }
    }

    suspend fun generateMotivationalContent(
        motivationType: String,
        energyLevel: Int?,
        additionalNotes: String
    ): String {
        val prompt = buildString {
            append("Generate a short encouraging message to help someone improve their fruit intake. ")
            if (motivationType.isNotBlank()) {
                append("Can give tips about $motivationType. ")
            }
            if (energyLevel != null) {
                append("The user's energy level is approximately $energyLevel out of 5. ")
            }
            if (additionalNotes.isNotBlank()) {
                append("Here are some additional notes from the user: $additionalNotes. ")
            }
            append("Keep it encouraging, and actionable, it can be long. Maximum 50 words")
        }

        return try {
            val response = generativeModel.generateContent(
                content {
                    text(prompt)
                }
            )
            response.text ?: "Could not generate a motivational message."
        } catch (e: Exception) {
            e.localizedMessage ?: "Error generating motivational message."
        }
    }

    fun deleteInsightAt(index: Int) {
        if (index in _insights.indices) {
            _insights.removeAt(index)
        }
    }

    fun clearInsights() {
        _insights.clear()
        clickCount = 0
        _uiState.value = UiState.Initial
    }
}

class GenAIViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(GenAIViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return GenAIViewModel(application) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
