package com.fit2081.aaron_34076832.nutritrack.data.questionnaire

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.PrimaryKey
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import com.fit2081.aaron_34076832.nutritrack.data.persona.Persona


@Entity(
    tableName = "questionnaire",
    foreignKeys = [ForeignKey(
        entity = Patient::class,
        parentColumns = ["userID"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )]
)
data class Questionnaire(
    @PrimaryKey //
    @ColumnInfo(name = "patientId")
    val patientId: String,

    var fruits: Boolean = false,
    var redMeat: Boolean = false,
    var fish: Boolean = false,
    var vegetables: Boolean = false,
    var seafood: Boolean = false,
    var eggs: Boolean = false,
    var grains: Boolean = false,
    var poultry: Boolean = false,
    var nutsSeeds: Boolean = false,

    val persona: Persona? = null,
    var timeMeal: String? = null,
    var timeSleep: String? = null,
    var timeWakeUp: String? = null,

    var isCompleted: Boolean = false
)