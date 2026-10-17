package com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface NutriCoachTipsDao {
    @Insert
    suspend fun insert(tip: NutriCoachTips)

    @Query("SELECT * FROM nutri_coach_tips WHERE userId = :userId ORDER BY timestamp DESC")
    fun getAllTipsForUser(userId: String): Flow<List<NutriCoachTips>>

    @Query("DELETE FROM nutri_coach_tips WHERE userId = :userId")
    suspend fun deleteAllTipsForUser(userId: String)

    @Query("DELETE FROM nutri_coach_tips WHERE id = :tipId")
    suspend fun deleteTipById(tipId: Long)
}
