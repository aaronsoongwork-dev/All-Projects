package com.fit2081.aaron_34076832.nutritrack.data.foodIntake

import android.content.Context
import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase
import kotlinx.coroutines.flow.Flow

class FoodIntakeRepository(context: Context) {
    private val foodIntakeDao = AppDatabase.getDatabase(context).foodIntakeDao()

    val allIntakes: Flow<List<FoodIntake>> = foodIntakeDao.getAllFoodIntakes()

    suspend fun insert(foodIntake: FoodIntake) {
        foodIntakeDao.insertFoodIntake(foodIntake)
    }

    fun getFoodIntakeByPatientId(patientId: String): Flow<List<FoodIntake>> {
        return foodIntakeDao.getFoodIntakeByPatientId(patientId)
    }

    // NEW METHOD: Get the latest single food intake
    fun getLatestFoodIntakeByPatientId(patientId: String): Flow<FoodIntake?> {
        return foodIntakeDao.getLatestFoodIntakeByPatientId(patientId)
    }
}