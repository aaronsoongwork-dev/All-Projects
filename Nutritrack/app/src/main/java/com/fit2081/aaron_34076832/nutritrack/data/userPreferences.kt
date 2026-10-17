package com.fit2081.aaron_34076832.nutritrack.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.userPreferencesDataStore: DataStore<Preferences> by preferencesDataStore(name = "user_prefs")

class UserPreferencesManager(private val context: Context) {

    private val dataStore = context.userPreferencesDataStore

    private object PreferencesKeys {
        val IS_LOGGED_IN = booleanPreferencesKey("is_logged_in")
        val LAST_SCREEN_ROUTE = stringPreferencesKey("last_screen_route")
        val CURRENT_USER_ID = stringPreferencesKey("current_user_id")
    }

    val isLoggedIn: Flow<Boolean> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.IS_LOGGED_IN] ?: false
        }

    suspend fun setLoggedIn(loggedIn: Boolean) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.IS_LOGGED_IN] = loggedIn
        }
    }

    val lastScreenRoute: Flow<String?> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.LAST_SCREEN_ROUTE]
        }

    suspend fun setLastScreenRoute(route: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.LAST_SCREEN_ROUTE] = route
        }
    }

    val currentUserId: Flow<String?> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.CURRENT_USER_ID]
        }

    suspend fun setCurrentUserId(userId: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.CURRENT_USER_ID] = userId
        }
    }
}
