package com.fit2081.aaron_34076832.nutritrack.network

import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Path
//https://www.fruityvice.com/api/fruit/all

interface APIService {

    @GET("api/fruit/all")
    suspend fun getAllFruits(): Response<List<Fruit>>

    @GET("api/fruit/{fruitName}")
    suspend fun getFruitDetails(@Path("fruitName") fruitName: String): Response<Fruit>

    companion object {
        private const val BASE_URL = "https://www.fruityvice.com/"

        fun create(): APIService {
            val retrofit = Retrofit.Builder()
                .addConverterFactory(GsonConverterFactory.create())
                .baseUrl(BASE_URL)
                .build()
            return retrofit.create(APIService::class.java)
        }
    }
}
