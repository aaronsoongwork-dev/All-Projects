package com.fit2081.aaron_34076832.nutritrack.viewmodels

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader

class HomeScreenViewModel(application: Application) : AndroidViewModel(application) {

    private val patientRepository: PatientRepository = PatientRepository(application)

    private val _userName = MutableLiveData<String>()
    val userName: LiveData<String> = _userName

    private val _foodQualityScore = MutableLiveData<String>()
    val foodQualityScore: LiveData<String> = _foodQualityScore

    private var currentUserId: String = ""

    fun setUserId(userId: String) {
        if (currentUserId != userId) {
            currentUserId = userId
            fetchUserData(userId)
            fetchFoodQualityScore(userId)
        }
    }

    private fun fetchUserData(userId: String) {
        viewModelScope.launch {
            val patient = withContext(Dispatchers.IO) {
                patientRepository.getPatientById(userId)
            }
            _userName.postValue(patient?.userName ?: "Unknown User")
        }
    }

    private fun fetchFoodQualityScore(userId: String) {
        viewModelScope.launch {
            val score = withContext(Dispatchers.IO) {
                readFoodQualityScoreFromFile(getApplication<Application>().applicationContext, userId)
            }
            _foodQualityScore.postValue(score)
        }
    }

    private fun readFoodQualityScoreFromFile(context: Context, userID: String): String {
        var healthScore = "N/A"
        try {
            val inputStream = context.assets.open("dataset.csv")
            val reader = BufferedReader(InputStreamReader(inputStream))
            reader.useLines { lines ->
                for (line in lines.drop(1)) {
                    val values = line.split(",")
                    if (values.size > 4 && values[1].trim() == userID.trim()) {
                        healthScore = if (values[2].trim() == "Female") {
                            values[4].trim()
                        } else {
                            values[3].trim()
                        }
                        break
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return healthScore
    }

    class HomeViewModelFactory(private val application: Application) :
        androidx.lifecycle.ViewModelProvider.Factory {
        override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(HomeScreenViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return HomeScreenViewModel(application) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}