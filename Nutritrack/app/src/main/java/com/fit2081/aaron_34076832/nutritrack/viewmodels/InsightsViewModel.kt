package com.fit2081.aaron_34076832.nutritrack.data.insights

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeRepository
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeViewModel

class InsightsViewModel(application: Application) : AndroidViewModel(application) {

    private val foodIntakeRepository: FoodIntakeRepository = FoodIntakeRepository(application)
    private val _foodIntakeViewModel: FoodIntakeViewModel = FoodIntakeViewModel(application)
    val foodIntakeViewModel: FoodIntakeViewModel = _foodIntakeViewModel

    private val _showShareDialog = MutableLiveData(false)
    val showShareDialog: LiveData<Boolean> = _showShareDialog

    private val _shareMessage = MutableLiveData("")
    val shareMessage: LiveData<String> = _shareMessage

    fun setShowShareDialog(show: Boolean) {
        _showShareDialog.value = show
    }

    fun setShareMessage(message: String) {
        _shareMessage.value = message
    }

    class InsightsViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(InsightsViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return InsightsViewModel(application) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}