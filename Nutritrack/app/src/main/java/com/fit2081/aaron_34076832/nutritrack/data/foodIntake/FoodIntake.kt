package com.fit2081.aaron_34076832.nutritrack.data.foodIntake

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.PrimaryKey
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient

@Entity(
    tableName = "food_intake",
    foreignKeys = [ForeignKey(
        entity = Patient::class,
        parentColumns = ["userID"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )]
)
data class FoodIntake(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0, // <-- Required by Room

    @ColumnInfo(index = true) // recommended for foreign keys
    val patientId: String, // FK referencing Patient.userID

    val heiFATotalscore: Double?,
    val discretionaryHEIFAscore: Int?,
    val discretionaryservesize: Double?,
    val vegetablesHEIFAscore: Double?,
    val vegetableswithlegumesallocatedservesize: Double?,
    val legumesallocatedVegetables: Int?,
    val vegetablesvariationsscore: Int?,
    val vegetablesCruciferous: Int?,
    val vegetablesTuberandbulb: Int?,
    val vegetablesOther: Int?,
    val legumes: Double?,
    val vegetablesGreen: Double?,
    val vegetablesRedandorange: Double?,
    val fruitHEIFAscore: Double?,
    val fruitservesize: Double?,
    val fruitvariationsscore: Int?,
    val fruitPome: Int?,
    val fruitTropicalandsubtropical: Int?,
    val fruitBerry: Int?,
    val fruitStone: Int?,
    val fruitCitrus: Int?,
    val fruitOther: Int?,
    val grainsandcerealsHEIFAscore: Double?,
    val grainsandcerealsservesize: Double?,
    val grainsandcerealsNonwholegrains: Double?,
    val wholegrainsHEIFAscore: Double?,
    val wholegrainsservesize: Double?,
    val meatandalternativesHEIFAscore: Int?,
    val meatandalternativeswithlegumesallocatedservesize: Double?,
    val legumesallocatedMeatandalternatives: Int?,
    val dairyandalternativesHEIFAscore: Int?,
    val dairyandalternativesservesize: Double?,
    val sodiumHEIFAscore: Int?,
    val sodiummgmilligrams: Double?,
    val alcoholHEIFAscore: Int?,
    val alcoholstandarddrinks: Int?,
    val waterHEIFAscore: Int?,
    val water: Double?,
    val waterTotalmL: Double?,
    val beverageTotalmL: Double?,
    val sugarHEIFAscore: Int?,
    val sugar: Double?,
    val saturatedFatHEIFAscore: Int?,
    val saturatedFat: Double?,
    val unsaturatedFatHEIFAscore: Double?,
    val unsaturatedFatservesize: Double?,

    )
