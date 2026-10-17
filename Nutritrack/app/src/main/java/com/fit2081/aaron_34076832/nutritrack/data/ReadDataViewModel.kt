package com.fit2081.aaron_34076832.nutritrack.data

import android.content.Context
import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntake
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeRepository
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.BufferedReader
import java.io.InputStreamReader

class ReadDataViewModel(
    private val patientRepository: PatientRepository,
    private val foodIntakeRepository: FoodIntakeRepository
) : ViewModel() {

    companion object {
        private const val PREFS_NAME = "prefs"
        private const val KEY_LAST_LOADED_DB_VERSION = "last_loaded_db_version"
        private const val CURRENT_DB_VERSION = 24
        private const val TAG = "CSV_IMPORT"
    }

    private val _csvLoadStatus = MutableLiveData<String>()

    private fun List<String>.safeGetDouble(headerMap: Map<String, Int>, key: String): Double? =
        this.getOrNull(headerMap[key] ?: -1)?.toDoubleOrNull()

    private fun List<String>.safeGetInt(headerMap: Map<String, Int>, key: String): Int? =
        this.getOrNull(headerMap[key] ?: -1)?.toIntOrNull()

    private fun List<String>.safeGetString(headerMap: Map<String, Int>, key: String): String =
        this.getOrElse(headerMap[key] ?: -1) { "" }

    fun readAndSaveCsvFromAssets(context: Context, fileName: String = "dataset.csv") {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val lastLoadedVersion = prefs.getInt(KEY_LAST_LOADED_DB_VERSION, -1)

        if (lastLoadedVersion == CURRENT_DB_VERSION) {
            Log.i(TAG, "CSV already loaded for DB version $CURRENT_DB_VERSION, skipping import.")
            _csvLoadStatus.postValue("CSV already loaded for DB version $CURRENT_DB_VERSION.")
            return
        }

        viewModelScope.launch(Dispatchers.IO) {
            try {
                val inputStream = context.assets.open(fileName)
                val reader = BufferedReader(InputStreamReader(inputStream))

                val header = reader.readLine()?.split(",") ?: run {
                    Log.e(TAG, "Header line missing.")
                    _csvLoadStatus.postValue("CSV header missing.")
                    return@launch
                }
                val headerMap = header.withIndex().associate { it.value.trim() to it.index }

                val lines = reader.lineSequence().toList()
                Log.i(TAG, "CSV lines read: ${lines.size}")

                var patientCount = 0
                var foodCount = 0

                for ((index, line) in lines.withIndex()) {
                    val tokens = line.split(",")

                    val userIdIndex = headerMap["User_ID"] ?: continue
                    if (tokens.size <= userIdIndex) {
                        Log.w(TAG, "Skipping line $index due to missing User_ID")
                        continue
                    }

                    Log.i(TAG, "Parsed patient: userID=${tokens[userIdIndex]}, userPhoneNum=${tokens.safeGetString(headerMap, "PhoneNumber").toLongOrNull()}")

                    val patient = try {
                        Patient(
                            userID = tokens[userIdIndex],
                            userPhoneNum = tokens.safeGetString(headerMap, "PhoneNumber").toLongOrNull(),
                            userSex = Gender.valueOf(tokens.safeGetString(headerMap, "Sex").uppercase())
                        )
                    } catch (e: Exception) {
                        Log.w(TAG, "Skipping patient at line $index: ${e.message}")
                        continue
                    }

                    val isMale = patient.userSex == Gender.MALE

                    val foodIntake = try {
                        FoodIntake(
                            patientId = patient.userID,
                            heiFATotalscore = tokens.safeGetDouble(headerMap, if (isMale) "HEIFAtotalscoreMale" else "HEIFAtotalscoreFemale"),
                            discretionaryHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "DiscretionaryHEIFAscoreMale" else "DiscretionaryHEIFAscoreFemale"),
                            discretionaryservesize = tokens.safeGetDouble(headerMap, "Discretionaryservesize"),
                            vegetablesHEIFAscore = tokens.safeGetDouble(headerMap, if (isMale) "VegetablesHEIFAscoreMale" else "VegetablesHEIFAscoreFemale"),
                            vegetableswithlegumesallocatedservesize = tokens.safeGetDouble(headerMap, "Vegetableswithlegumesallocatedservesize"),
                            legumesallocatedVegetables = tokens.safeGetInt(headerMap, "LegumesallocatedVegetables"),
                            vegetablesvariationsscore = tokens.safeGetInt(headerMap, "Vegetablesvariationsscore"),
                            vegetablesCruciferous = tokens.safeGetInt(headerMap, "VegetablesCruciferous"),
                            vegetablesTuberandbulb = tokens.safeGetInt(headerMap, "VegetablesTuberandbulb"),
                            vegetablesOther = tokens.safeGetInt(headerMap, "VegetablesOther"),
                            legumes = tokens.safeGetDouble(headerMap, "Legumes"),
                            vegetablesGreen = tokens.safeGetDouble(headerMap, "VegetablesGreen"),
                            vegetablesRedandorange = tokens.safeGetDouble(headerMap, "VegetablesRedandorange"),
                            fruitHEIFAscore = tokens.safeGetDouble(headerMap, if (isMale) "FruitHEIFAscoreMale" else "FruitHEIFAscoreFemale"),
                            fruitservesize = tokens.safeGetDouble(headerMap, "Fruitservesize"),
                            fruitvariationsscore = tokens.safeGetInt(headerMap, "Fruitvariationsscore"),
                            fruitPome = tokens.safeGetInt(headerMap, "FruitPome"),
                            fruitTropicalandsubtropical = tokens.safeGetInt(headerMap, "FruitTropicalandsubtropical"),
                            fruitBerry = tokens.safeGetInt(headerMap, "FruitBerry"),
                            fruitStone = tokens.safeGetInt(headerMap, "FruitStone"),
                            fruitCitrus = tokens.safeGetInt(headerMap, "FruitCitrus"),
                            fruitOther = tokens.safeGetInt(headerMap, "FruitOther"),
                            grainsandcerealsHEIFAscore = tokens.safeGetDouble(headerMap, if (isMale) "GrainsandcerealsHEIFAscoreMale" else "GrainsandcerealsHEIFAscoreFemale"),
                            grainsandcerealsservesize = tokens.safeGetDouble(headerMap, "Grainsandcerealsservesize"),
                            grainsandcerealsNonwholegrains = tokens.safeGetDouble(headerMap, "GrainsandcerealsNonwholegrains"),
                            wholegrainsHEIFAscore = tokens.safeGetDouble(headerMap, if (isMale) "WholegrainsHEIFAscoreMale" else "WholegrainsHEIFAscoreFemale"),
                            wholegrainsservesize = tokens.safeGetDouble(headerMap, "Wholegrainsservesize"),
                            meatandalternativesHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "MeatandalternativesHEIFAscoreMale" else "MeatandalternativesHEIFAscoreFemale"),
                            meatandalternativeswithlegumesallocatedservesize = tokens.safeGetDouble(headerMap, "Meatandalternativeswithlegumesallocatedservesize"),
                            legumesallocatedMeatandalternatives = tokens.safeGetInt(headerMap, "LegumesallocatedMeatandalternatives"),
                            dairyandalternativesHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "DairyandalternativesHEIFAscoreMale" else "DairyandalternativesHEIFAscoreFemale"),
                            dairyandalternativesservesize = tokens.safeGetDouble(headerMap, "Dairyandalternativesservesize"),
                            sodiumHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "SodiumHEIFAscoreMale" else "SodiumHEIFAscoreFemale"),
                            sodiummgmilligrams = tokens.safeGetDouble(headerMap, "Sodiummgmilligrams"),
                            alcoholHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "AlcoholHEIFAscoreMale" else "AlcoholHEIFAscoreFemale"),
                            alcoholstandarddrinks = tokens.safeGetInt(headerMap, "Alcoholstandarddrinks"),
                            waterHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "WaterHEIFAscoreMale" else "WaterHEIFAscoreFemale"),
                            water = tokens.safeGetDouble(headerMap, "Water"),
                            waterTotalmL = tokens.safeGetDouble(headerMap, "WaterTotalmL"),
                            beverageTotalmL = tokens.safeGetDouble(headerMap, "BeverageTotalmL"),
                            sugarHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "SugarHEIFAscoreMale" else "SugarHEIFAscoreFemale"),
                            sugar = tokens.safeGetDouble(headerMap, "Sugar"),
                            saturatedFatHEIFAscore = tokens.safeGetInt(headerMap, if (isMale) "SaturatedFatHEIFAscoreMale" else "SaturatedFatHEIFAscoreFemale"),
                            saturatedFat = tokens.safeGetDouble(headerMap, "SaturatedFat"),
                            unsaturatedFatHEIFAscore = tokens.safeGetDouble(headerMap, if (isMale) "UnsaturatedFatHEIFAscoreMale" else "UnsaturatedFatHEIFAscoreFemale"),
                            unsaturatedFatservesize = tokens.safeGetDouble(headerMap, "UnsaturatedFatservesize")
                        )
                    } catch (e: Exception) {
                        Log.w(TAG, "Skipping food intake at line $index: ${e.message}")
                        continue
                    }

                    try {
                        patientRepository.insertPatient(patient)
                        foodIntakeRepository.insert(foodIntake)
                        patientCount++
                        foodCount++
                    } catch (e: Exception) {
                        Log.e(TAG, "Insert error at line $index: ${e.message}")
                    }
                }

                prefs.edit().putInt(KEY_LAST_LOADED_DB_VERSION, CURRENT_DB_VERSION).apply()
                _csvLoadStatus.postValue("CSV Loaded: $patientCount patients, $foodCount food records")
                Log.i(TAG, "CSV processing complete.")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to load CSV: ${e.message}")
                _csvLoadStatus.postValue("CSV load failed: ${e.message}")
            }
        }
    }
}
