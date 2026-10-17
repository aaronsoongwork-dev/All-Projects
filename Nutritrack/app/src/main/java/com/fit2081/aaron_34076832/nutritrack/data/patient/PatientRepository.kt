package com.fit2081.aaron_34076832.nutritrack.data.patient

import android.content.Context
import androidx.lifecycle.LiveData
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase
import kotlinx.coroutines.flow.Flow

class PatientRepository(context: Context) {

    private val patientDao = AppDatabase.getDatabase(context).patientDao()

    suspend fun insertPatient(patient: Patient) {
        patientDao.insertPatient(patient)
    }

    suspend fun getPatientById(userId: String): Patient {
        return patientDao.getPatientById(userId)
    }

    fun getAllPatients(): Flow<List<Patient>> = patientDao.getAllPatients()

    fun getAllUserIds(): LiveData<List<String>> = patientDao.getAllUserIds()

    suspend fun getPatientID(): String? {
        return patientDao.getPatientID()
    }

    suspend fun getPatientPassword(userId: String): String? {
        return patientDao.getPatientPassword(userId)
    }

    suspend fun updatePatient(patient: Patient) {
        patientDao.updatePatient(patient)
    }

    suspend fun getGenderByUserId(userId: String): Gender? = patientDao.getGenderByUserId(userId)

    suspend fun getUserNameByUserId(userId: String): String? {
        return patientDao.getUserNameByUserId(userId)
    }

}
