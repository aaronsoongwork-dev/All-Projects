package com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "nutri_coach_tips")
data class NutriCoachTips(
    val userId: String, // userId should NOT be auto-generated
    @PrimaryKey(autoGenerate = true) // autoGenerate should be on id
    val id: Long = 0L,
    val message: String,
    val timestamp: Long = System.currentTimeMillis()
)