package com.fit2081.aaron_34076832.nutritrack.data.persona

import androidx.room.TypeConverter

class PersonaConverter {
    @TypeConverter
    fun fromPersona(persona: Persona?): String? = persona?.name

    @TypeConverter
    fun toPersona(value: String?): Persona? = value?.let { Persona.valueOf(it) }
}