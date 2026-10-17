package com.fit2081.aaron_34076832.nutritrack.screens

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.R
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen
import com.fit2081.aaron_34076832.nutritrack.viewmodels.HomeScreenViewModel

class HomeScreen : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val userId = intent.getStringExtra("user_id") ?: "Unknown ID"

        enableEdgeToEdge()
        setContent {
            A1HealthAppTheme {
            }

            val dContext = LocalContext.current
            val application = application

            val userPreferencesManager = remember { UserPreferencesManager(dContext.applicationContext) }

            LaunchedEffect(Unit) {
                userPreferencesManager.setLastScreenRoute("home_screen")
            }

            val homeViewModel: HomeScreenViewModel = viewModel(
                factory = HomeScreenViewModel.HomeViewModelFactory(application)
            )

            val userName by homeViewModel.userName.observeAsState("Loading...")
            val foodQualityScore by homeViewModel.foodQualityScore.observeAsState("N/A")

            LaunchedEffect(userId) {
                homeViewModel.setUserId(userId)
            }

            Scaffold(modifier = Modifier.fillMaxSize(),
                bottomBar = { MyBottomBarHome(dContext, userId, "Home") }
            ) { innerPadding ->

                val context = LocalContext.current

                Column(
                    modifier = Modifier
                        .padding(innerPadding)
                        .fillMaxHeight()
                        .padding(horizontal = 24.dp),
                    verticalArrangement = Arrangement.Top,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Spacer(modifier = Modifier.height(24.dp))

                    Text(
                        text = "Hello,",
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Left,
                        fontSize = 16.sp,
                        color = Color.Gray,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Text(
                        text = userName,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Left,
                        fontSize = 28.sp,
                        color = Color.Black,
                        modifier = Modifier
                            .padding(bottom = 2.dp)
                            .fillMaxWidth()
                    )

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Spacer(modifier = Modifier.height(8.dp))

                        Text(
                            "You've already filled in your Food Intake\n" +
                                    "Questionnaire, but you can change \ndetails here:",
                            textAlign = TextAlign.Left,
                            fontSize = 13.sp,
                            lineHeight = 16.sp
                        )

                        Spacer(Modifier.width(30.dp))

                        Button(
                            shape = RoundedCornerShape(12.dp),
                            onClick = {
                                val intent = Intent(context, Questionaire::class.java)
                                intent.putExtra("user_id", userId)
                                Toast.makeText(
                                    context,
                                    "Returning to Edit Details!",
                                    Toast.LENGTH_LONG
                                ).show()
                                context.startActivity(intent)
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
                        ) {
                            Text(text = "✏️  Edit")
                        }
                    }

                    Image(
                        painter = painterResource(id = R.drawable.balanceddiet),
                        contentDescription = "Photo of Balanced Diet",
                        modifier = Modifier
                            .size(300.dp)
                            .fillMaxWidth(0.85f),
                    )

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = "My Score",
                            fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Left,
                            fontSize = 22.sp,
                            color = Color.Black,
                        )

                        Spacer(Modifier.width(160.dp))

                        Text(
                            text = "See all scores >",
                            color = Color.Gray,
                            fontSize = 14.sp,
                            textAlign = TextAlign.Left,
                            modifier = Modifier.clickable {
                                val intent = Intent(context, Insights::class.java)
                                intent.putExtra("user_id", userId)
                                context.startActivity(intent)
                            }
                        )
                    }

                    Spacer(Modifier.height(8.dp))

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Image(
                            painter = painterResource(id = R.drawable.up_arrow),
                            contentDescription = "Arrow Up",
                            modifier = Modifier.size(30.dp)
                        )

                        Spacer(Modifier.width(20.dp))

                        Text(
                            text = "Your Food Quality Score",
                            color = Color.Black,
                            fontSize = 16.sp
                        )

                        Spacer(Modifier.width(60.dp))

                        Text(
                            text = "${foodQualityScore}/100",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF4CAF50)
                        )
                    }

                    Row(
                        modifier = Modifier.padding(2.dp),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Spacer(Modifier.height(40.dp))
                        Text(" - - - - - - - - - - - - - - - - ")
                    }

                    Column(
                        modifier = Modifier.padding(2.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Spacer(Modifier.height(4.dp))

                        Text(
                            text = "What is the Food Quality Score?",
                            fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Left,
                            modifier = Modifier.fillMaxWidth(),
                            fontSize = 20.sp,
                        )

                        Spacer(Modifier.height(8.dp))

                        Text(
                            text = "Your Food Quality Score provides a snapshot of how well" +
                                    " your eating patterns align with established food" +
                                    " guidelines, helping you identify both strengths and" +
                                    " opportunities for improvement in your diet. \n\n" +
                                    "This personalized measurement considers various food " +
                                    "groups including vegetables, fruits, whole grains, " +
                                    "and proteins to give you practical insights for making " +
                                    "healthier food choices.",
                            fontSize = 13.sp,
                            textAlign = TextAlign.Left,
                            lineHeight = 16.sp,
                        )
                    }
                }
            }
        }
    }
}


@Composable
fun MyBottomBarHome(context: Context, userID: String?, currentScreen: String) {
    BottomAppBar(
        modifier = Modifier.height(100.dp),
        content = {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, HomeScreen::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Home, contentDescription = "Go Home",
                            tint = if (currentScreen == "Home") CustomBrown else
                                LocalContentColor.current)
                    }
                    Text("Home",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Home") CustomBrown else
                            LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, Insights::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Favorite, contentDescription = "Insights",
                            tint = if (currentScreen == "Insights") CustomBrown else
                                LocalContentColor.current)
                    }
                    Text("Insights",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Insights") CustomBrown else
                            LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, NutriCoach::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Face, contentDescription = "NutriCoach",
                            tint = if (currentScreen == "NutriCoach") CustomBrown else
                                LocalContentColor.current)
                    }
                    Text("NutriCoach",
                        fontSize = 11.sp,
                        color = if (currentScreen == "NutriCoach") CustomBrown else
                            LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, Settings::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings",
                            tint = if (currentScreen == "Settings") CustomBrown else
                                LocalContentColor.current
                        )
                    }
                    Text(
                        "Settings",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Settings") CustomBrown else
                            LocalContentColor.current
                    )
                }
            }
        }
    )
}