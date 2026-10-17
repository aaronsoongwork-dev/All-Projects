package com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips

import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase
import kotlinx.coroutines.flow.Flow

class NutriCoachTipsRepository(private val database: AppDatabase) {
    private val nutriCoachTipsDao = database.nutriCoachTipsDao()


    suspend fun insertTip(tip: NutriCoachTips) {
        nutriCoachTipsDao.insert(tip)
    }


    suspend fun deleteTipById(tipId: Long) {
        nutriCoachTipsDao.deleteTipById(tipId)
    }

    fun getAllTipsForUser(userId: String): Flow<List<NutriCoachTips>> {
        return nutriCoachTipsDao.getAllTipsForUser(userId)
    }

    suspend fun deleteAllTipsForUser(userId: String) {
        nutriCoachTipsDao.deleteAllTipsForUser(userId)
    }
}