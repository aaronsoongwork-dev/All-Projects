package com.fit2081.aaron_34076832.nutritrack.screens

import android.content.Context
import android.content.Intent
import android.content.Intent.ACTION_SEND
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.data.insights.InsightsViewModel
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen

class Insights : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val userId = intent.getStringExtra("user_id") ?: "Unknown ID"

        enableEdgeToEdge()
        setContent {
            A1HealthAppTheme {
                val context = LocalContext.current
                val application = application

                val userPreferencesManager = remember { UserPreferencesManager(context.applicationContext) }
                LaunchedEffect(Unit) {
                    userPreferencesManager.setLastScreenRoute("insights")
                }

                val insightsViewModel: InsightsViewModel = viewModel(
                    factory = InsightsViewModel.InsightsViewModelFactory(application)
                )

                Scaffold(modifier = Modifier.fillMaxSize(),
                    bottomBar = { MyBottomBar(context, userId, "Insights") },
                    topBar = { TopAppBarInsights() }

                ) { innerPadding ->
                    InsightsScreenContent(
                        modifier = Modifier.padding(innerPadding),
                        context,
                        userId,
                        insightsViewModel
                    )
                }
            }
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun TopAppBarInsights() {
        CenterAlignedTopAppBar(
            colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                containerColor = CustomBrown,
                titleContentColor = Color.White
            ),
            title = {
                Text(
                    text = "Insights: Food Score",
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    fontSize = 24.sp,
                    modifier = Modifier
                        .padding(bottom = 2.dp)
                        .fillMaxWidth()
                )
            }
        )
    }
}

@Composable
fun MyBottomBar(context: Context, userID: String?, currentScreen: String) {
    BottomAppBar(
        modifier = Modifier.height(100.dp),
        content = {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, HomeScreen::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Home, contentDescription = "Go Home",
                            tint = if (currentScreen == "Home") CustomBrown
                            else LocalContentColor.current)
                    }
                    Text("Home",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Home") CustomBrown
                        else LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, Insights::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Favorite, contentDescription = "Insights",
                            tint = if (currentScreen == "Insights") CustomBrown
                            else LocalContentColor.current)
                    }
                    Text("Insights",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Insights") CustomBrown
                        else LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, NutriCoach::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Face, contentDescription = "NutriCoach",
                            tint = if (currentScreen == "NutriCoach") CustomBrown
                            else LocalContentColor.current)
                    }
                    Text("NutriCoach",
                        fontSize = 11.sp,
                        color = if (currentScreen == "NutriCoach") CustomBrown
                        else LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, Settings::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings",
                            tint = if (currentScreen == "Settings") CustomBrown
                            else LocalContentColor.current
                        )
                    }
                    Text(
                        "Settings",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Settings") CustomBrown
                        else LocalContentColor.current
                    )
                }
            }
        }
    )
}


@Composable
fun InsightsScreenContent(modifier: Modifier, context: Context, userId : String, insightsViewModel: InsightsViewModel) {
    Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
        Column(
            modifier = modifier
                .padding(innerPadding)
                .fillMaxHeight()
                .padding(horizontal = 24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.Top,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            val foodIntakes by insightsViewModel.foodIntakeViewModel.getFoodIntakeByPatientId(userId).collectAsState(initial = emptyList())

            val latestFoodIntake = foodIntakes.lastOrNull()

            val vegetablesScore = latestFoodIntake?.vegetablesHEIFAscore?.toString() ?: "0"
            val fruitsScore = latestFoodIntake?.fruitHEIFAscore?.toString() ?: "0"
            val grainsCerealsScore = latestFoodIntake?.grainsandcerealsHEIFAscore?.toString() ?: "0"
            val wholeGrainsScore = latestFoodIntake?.wholegrainsHEIFAscore?.toString() ?: "0"
            val meatAlternativesScore = latestFoodIntake?.meatandalternativesHEIFAscore?.toString() ?: "0"
            val dairyScore = latestFoodIntake?.dairyandalternativesHEIFAscore?.toString() ?: "0"
            val waterScore = latestFoodIntake?.waterHEIFAscore?.toString() ?: "0"
            val saturatedFatsScore = latestFoodIntake?.saturatedFatHEIFAscore?.toString() ?: "0"
            val unsaturatedFatsScore = latestFoodIntake?.unsaturatedFatHEIFAscore?.toString() ?: "0"
            val sodiumScore = latestFoodIntake?.sodiumHEIFAscore?.toString() ?: "0"
            val sugarScore = latestFoodIntake?.sugarHEIFAscore?.toString() ?: "0"
            val alcoholScore = latestFoodIntake?.alcoholHEIFAscore?.toString() ?: "0"
            val discretionaryFoodsScore = latestFoodIntake?.discretionaryHEIFAscore?.toString() ?: "0"
            val totalFoodQualityScore = latestFoodIntake?.heiFATotalscore?.toString() ?: "0"

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Food Items",
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    modifier = Modifier.weight(1.5f)
                )
                Text(
                    text = "Food Score",
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    textAlign = TextAlign.End,
                    modifier = Modifier.weight(1.5f).padding(end = 8.dp)
                )
            }

            Spacer(modifier = Modifier.height(2.dp))

            HorizontalDivider(
                modifier = Modifier
                    .fillMaxWidth(),
                thickness = 1.dp,
                color = Color.LightGray
            )

            Spacer(modifier = Modifier.height(2.dp))

            CreateFoodSlider("Vegetables", vegetablesScore, 10)
            CreateFoodSlider("Fruits", fruitsScore, 10)
            CreateFoodSlider("Grains & Cereals", grainsCerealsScore, 5)
            CreateFoodSlider("Whole Grains", wholeGrainsScore, 5)
            CreateFoodSlider("Meat & Alternatives", meatAlternativesScore, 10)
            CreateFoodSlider("Dairy", dairyScore, 10)
            CreateFoodSlider("Water", waterScore, 5)
            CreateFoodSlider("Saturated Fats", saturatedFatsScore, 5)
            CreateFoodSlider("Unsaturated Fats", unsaturatedFatsScore, 5)
            CreateFoodSlider("Sodium", sodiumScore, 10)
            CreateFoodSlider("Sugar", sugarScore, 10)
            CreateFoodSlider("Alcohol", alcoholScore, 5)
            CreateFoodSlider("Discretionary Foods", discretionaryFoodsScore, 10)

            Spacer(modifier = Modifier.height(40.dp))

            TotalScoreSlider("Total Food Quality Score", totalFoodQualityScore)

            Row {
                ShowButtonAndModal("🪧 Share with someone!", context, totalFoodQualityScore, insightsViewModel)

                Spacer(modifier = Modifier.width(16.dp))

                Button(onClick = {
                    val intent = Intent(context, NutriCoach::class.java)
                    intent.putExtra("user_id", userId)
                    Toast.makeText(context, "Going to NutriCoach page!",
                        Toast.LENGTH_LONG).show()
                    context.startActivity(intent)
                },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = CustomBrown)
                ) {
                    Text(
                        text = "🚀 Improve!"
                    )
                }
            }

            Spacer(modifier = Modifier.height(100.dp))
        }
    }
}


@Composable
fun ShowButtonAndModal(stringNameModal: String, passedContext: Context, totalScore: String, insightsViewModel: InsightsViewModel) {
    val showDialog by insightsViewModel.showShareDialog.observeAsState(initial = false)
    val shareText by insightsViewModel.shareMessage.observeAsState(initial = "")

    Button(onClick = { insightsViewModel.setShowShareDialog(true) },
        colors = ButtonDefaults.buttonColors(containerColor = CustomBrown)
    ) {
        Text(stringNameModal)
    }

    if (showDialog) {
        AlertDialog(
            onDismissRequest = { insightsViewModel.setShowShareDialog(false) },
            title = {
                Column {
                    Text(
                        text = "Share with Someone!",
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp
                    )
                    Text(
                        text = "Your food score is $totalScore/100 :>",
                        fontSize = 14.sp
                    )
                }
            },

            text = {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    TextField(
                        value = shareText,
                        onValueChange = { insightsViewModel.setShareMessage(it) },
                        label = { Text("Add a message (optional)") },
                        placeholder = { Text("My Food Quality Score is $totalScore/100. " +
                                "Let's improve together!") },
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(16.dp))
                }
            },

            confirmButton = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Button(
                        onClick = { insightsViewModel.setShowShareDialog(false) },
                        colors = ButtonDefaults.buttonColors(containerColor = CustomBrown)
                    ) {
                        Text("Cancel")
                    }

                    Button(
                        onClick = {
                            val finalShareMessage = if (shareText.isBlank()) {
                                "My Food Quality Score is $totalScore/100. Let's improve together!"
                            } else {
                                "$shareText\nMy Food Quality Score is $totalScore/100."
                            }

                            val shareIntent = Intent(ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_TEXT, finalShareMessage)
                            }
                            passedContext.startActivity(
                                Intent.createChooser(shareIntent, "Share via")
                            )
                            insightsViewModel.setShowShareDialog(false)
                            insightsViewModel.setShareMessage("")
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = CustomBrown)
                    ) {
                        Text("Share")
                    }
                }
            }
        )
    }
}

@Composable
fun CreateFoodSlider(label: String, score: String, limit: Int) {
    val sliderPosition = score.toFloatOrNull() ?: 0f

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(
            text = label,
            fontSize = 14.sp,
            modifier = Modifier.weight(1.5f)
        )

        Slider(
            valueRange = 0f..limit.toFloat(),
            value = sliderPosition,
            onValueChange = {},
            steps = limit - 1,
            colors = SliderDefaults.colors(
                thumbColor = CustomGreen,
                activeTrackColor = Color.Green
            ),
            modifier = Modifier.weight(1.5f)
        )

        Text(
            text = "${score}/${limit}",
            fontSize = 14.sp,
            modifier = Modifier.padding(start = 8.dp)
        )
    }
}


@Composable
fun TotalScoreSlider(label: String, score: String) {
    val sliderPosition = score.toFloatOrNull() ?: 0f

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier
            .fillMaxWidth()
    ) {

        Text(
            text = label,
            fontSize = 20.sp,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Left,
            fontWeight = FontWeight.Bold,
        )

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Start,
            modifier = Modifier
                .fillMaxWidth(0.9f)
        )
        {
            Slider(
                value = sliderPosition,
                modifier = Modifier.weight(1f),
                onValueChange = {},
                valueRange = 0f..100f,
                steps = 4,
                colors = SliderDefaults.colors(
                    thumbColor = CustomGreen,
                    activeTrackColor = Color.Green
                ))

            Text(
                text = "${score}/100",
                fontSize = 14.sp,
                modifier = Modifier.padding(start = 12.dp),
                textAlign = TextAlign.End
            )
        }
    }
}