package com.fit2081.aaron_34076832.nutritrack.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters // <--- ADD THIS
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntake
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientDao
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeDao
import com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips.NutriCoachTips
import com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips.NutriCoachTipsDao
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.Questionnaire // <--- ADD THIS
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.QuestionnaireDao
import com.fit2081.aaron_34076832.nutritrack.data.persona.PersonaConverter // <--- ADD THIS

@Database(
    entities = [Patient::class, FoodIntake::class, Questionnaire::class, NutriCoachTips::class],
    version = 24,
    exportSchema = false
)

@TypeConverters(PersonaConverter::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun patientDao(): PatientDao
    abstract fun foodIntakeDao(): FoodIntakeDao
    abstract  fun questionnaireDao(): QuestionnaireDao
    abstract fun nutriCoachTipsDao(): NutriCoachTipsDao

    companion object {
        @Volatile
        private var Instance: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return Instance ?: synchronized(this) {
                Room.databaseBuilder(context, AppDatabase::class.java, "a1health_database")
                    .fallbackToDestructiveMigration()
                    .build()
                    .also { Instance = it }
            }
        }
    }
}