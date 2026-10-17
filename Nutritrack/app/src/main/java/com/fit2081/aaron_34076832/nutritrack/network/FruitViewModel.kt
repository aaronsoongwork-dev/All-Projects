package com.fit2081.aaron_34076832.nutritrack.network

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class FruitViewModel : ViewModel() {

    private val repository = FruitRepository(APIService.create())

    private val _fruit = MutableStateFlow<Fruit?>(null)
    val fruit: StateFlow<Fruit?> = _fruit

    fun loadFruitDetails(fruitName: String) {
        viewModelScope.launch {
            try {
                val response = repository.getFruitDetails(fruitName)
                if (response.isSuccessful) {
                    _fruit.value = response.body()
                } else {
                    Log.e("com.fit2081.aaron_34076832.nutritrack.network.FruitViewModel", "Error ${response.code()}")
                }
            } catch (e: Exception) {
                Log.e("com.fit2081.aaron_34076832.nutritrack.network.FruitViewModel", "Exception: ${e.message}")
            }
        }
    }
}
