package com.fit2081.aaron_34076832.nutritrack.data.patient

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.a1healthapp.data.Gender.GenderConverter

@Entity
@TypeConverters(GenderConverter::class)
data class Patient(
    @PrimaryKey val userID: String,
    val userName: String = "user",
    val userPassword: String = "",
    val userPhoneNum: Long? = null,
    val userSex: Gender? = null,
    val userAge: Int? = null,
    var isRegistered: Boolean = false
)
