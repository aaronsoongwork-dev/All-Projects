package com.fit2081.aaron_34076832.nutritrack.data
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository

/**
  */
class AuthManager(private val repository: PatientRepository) {
    private var currentUser: Patient? = null

    suspend fun login(userId: String, password: String): Boolean {
        val user = repository.getPatientById(userId)
        return if (user.userPassword == password) {
            currentUser = user

            true
        } else {
            false
        }
    }

    fun logout() {
        currentUser = null
    }
}


