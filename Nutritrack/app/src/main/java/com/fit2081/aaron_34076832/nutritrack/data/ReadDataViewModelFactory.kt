package com.fit2081.aaron_34076832.nutritrack.data

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeRepository
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository

class ReadDataViewModelFactory(
    private val patientRepository: PatientRepository,
    private val foodIntakeRepository: FoodIntakeRepository
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ReadDataViewModel::class.java)) {
            return ReadDataViewModel(patientRepository, foodIntakeRepository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
