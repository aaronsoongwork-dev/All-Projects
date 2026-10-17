package com.fit2081.aaron_34076832.nutritrack.viewmodels

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope

import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntake
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeRepository
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch

class ClinicianDashboardViewModel(application: Application) : AndroidViewModel(application) {

    private val foodIntakeRepository: FoodIntakeRepository = FoodIntakeRepository(application)
    private val patientRepository: PatientRepository = PatientRepository(application)

    private val _maleAverageHeifa = MutableStateFlow<Double?>(null)
    val maleAverageHeifa: StateFlow<Double?> = _maleAverageHeifa.asStateFlow()

    private val _femaleAverageHeifa = MutableStateFlow<Double?>(null)
    val femaleAverageHeifa: StateFlow<Double?> = _femaleAverageHeifa.asStateFlow()

    init {
        viewModelScope.launch {
            combine(
                foodIntakeRepository.allIntakes,
                patientRepository.getAllPatients()
            ) { foodIntakes: List<FoodIntake>, patients: List<Patient> ->
                val patientGenderMap = patients.associateBy({ it.userID }, { it.userSex })

                val maleScores = mutableListOf<Double>()
                val femaleScores = mutableListOf<Double>()

                foodIntakes.forEach { intake ->
                    val patientGender = patientGenderMap[intake.patientId]
                    intake.heiFATotalscore?.let { score ->
                        when (patientGender) {
                            Gender.MALE  -> maleScores.add(score)
                            Gender.FEMALE -> femaleScores.add(score)
                            null -> TODO()
                        }
                    }
                }

                val avgMale = if (maleScores.isNotEmpty()) maleScores.average() else null
                val avgFemale = if (femaleScores.isNotEmpty()) femaleScores.average() else null

                _maleAverageHeifa.value = avgMale
                _femaleAverageHeifa.value = avgFemale
            }.collect { }
        }
    }

    class ClinicianDashboardViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(ClinicianDashboardViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return ClinicianDashboardViewModel(application) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}