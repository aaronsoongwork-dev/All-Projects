package com.fit2081.a1healthapp.data.Gender

import androidx.room.TypeConverter

class GenderConverter {
    @TypeConverter
    fun fromGender(gender: Gender): String = gender.name

    @TypeConverter
    fun toGender(value: String): Gender = Gender.valueOf(value)
}
