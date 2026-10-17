package com.fit2081.aaron_34076832.nutritrack.network

import retrofit2.Response

class FruitRepository(private val api: APIService) {

    suspend fun getFruitDetails(fruitName: String): Response<Fruit> {
        return api.getFruitDetails(fruitName)
    }
}
