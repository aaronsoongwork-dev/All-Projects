package com.fit2081.aaron_34076832.nutritrack.data.foodIntake

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface FoodIntakeDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertFoodIntake(foodIntake: FoodIntake)

    @Query("SELECT * FROM food_intake WHERE patientId = :patientId ORDER BY id DESC LIMIT 1")
    fun getLatestFoodIntakeByPatientId(patientId: String): Flow<FoodIntake?>

    // Keep your existing method if needed elsewhere
    @Query("SELECT * FROM food_intake WHERE patientId = :patientId")
    fun getFoodIntakeByPatientId(patientId: String): Flow<List<FoodIntake>>

    @Query("SELECT * FROM food_intake")
    fun getAllFoodIntakes(): Flow<List<FoodIntake>>

}