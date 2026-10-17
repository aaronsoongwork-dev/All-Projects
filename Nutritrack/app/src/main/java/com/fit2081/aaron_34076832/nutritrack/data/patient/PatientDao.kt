package com.fit2081.aaron_34076832.nutritrack.data.patient

import androidx.lifecycle.LiveData
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import kotlinx.coroutines.flow.Flow

@Dao
interface PatientDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPatient(patient: Patient)

    @Query("SELECT * FROM Patient WHERE userID = :userId")
    suspend fun getPatientById(userId: String): Patient

    @Query("SELECT * FROM Patient")
    fun getAllPatients(): Flow<List<Patient>>

    @Query("SELECT userId FROM Patient")
    fun getAllUserIds(): LiveData<List<String>>

    @Query("SELECT userID FROM Patient LIMIT 1")
    suspend fun getPatientID(): String?

    @Query("SELECT userPassword FROM Patient WHERE userID = :userId")
    suspend fun getPatientPassword(userId: String): String?

    @Update
    suspend fun updatePatient(patient: Patient)

    @Query("SELECT userSex FROM patient WHERE userId = :userId LIMIT 1")
    suspend fun getGenderByUserId(userId: String): Gender?

    @Query("SELECT userName FROM Patient WHERE userID = :userId LIMIT 1")
    suspend fun getUserNameByUserId(userId: String): String

}
