package com.fit2081.aaron_34076832.nutritrack.data.foodIntake

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.launch

class FoodIntakeViewModel(context: Context) : ViewModel(){

    private val foodIntakeRepository : FoodIntakeRepository = FoodIntakeRepository(context)

    val allIntakes: Flow<List<FoodIntake>> = foodIntakeRepository.allIntakes;

    fun insertFoodIntake(foodIntake: FoodIntake) {
        viewModelScope.launch { foodIntakeRepository.insert(foodIntake) }
    }

    fun getFoodIntakeByPatientId(patientId: String):
            Flow<List<FoodIntake>> = foodIntakeRepository.getFoodIntakeByPatientId(patientId)

    fun getLatestFoodIntakeByPatientId(patientId: String):
            Flow<FoodIntake?> = foodIntakeRepository.getLatestFoodIntakeByPatientId(patientId)


    class FoodIntakeViewModelFactory(context: Context) : ViewModelProvider.Factory {
        private val context = context.applicationContext
        // Use application context to avoid memory leaks
        override fun <T : ViewModel> create(modelClass: Class<T>): T =
            FoodIntakeViewModel(context) as T
    }

}