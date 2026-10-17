package com.fit2081.aaron_34076832.nutritrack.screens

import android.annotation.SuppressLint
import android.app.Application
import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeViewModel
import com.fit2081.aaron_34076832.nutritrack.genAI.GenAIViewModel
import com.fit2081.aaron_34076832.nutritrack.genAI.GenAIViewModelFactory
import com.fit2081.aaron_34076832.nutritrack.genAI.UiState
import com.fit2081.aaron_34076832.nutritrack.viewmodels.ClinicianDashboardViewModel


class ClinicianDashboard : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            A1HealthAppTheme {
                val userId = intent.getStringExtra("user_id")
                val clinicianDashboardViewModel: ClinicianDashboardViewModel = viewModel(
                    factory = ClinicianDashboardViewModel.ClinicianDashboardViewModelFactory(
                        application
                    )
                )

                val averageMaleHeifa by clinicianDashboardViewModel.maleAverageHeifa.collectAsState(
                    initial = 0.0
                )
                val averageFemaleHeifa by clinicianDashboardViewModel.femaleAverageHeifa.collectAsState(
                    initial = 0.0
                )

                val context = LocalContext.current
                val userPreferencesManager = remember { UserPreferencesManager(context.applicationContext) }
                LaunchedEffect(Unit) {
                    userPreferencesManager.setLastScreenRoute("clinician_dashboard")
                }

                val genAIViewModel: GenAIViewModel = viewModel(factory = GenAIViewModelFactory(application))

                averageMaleHeifa?.let {
                    averageFemaleHeifa?.let { it1 ->
                        ClinicianDashboardContent(
                            context, userId,
                            it, it1, genAIViewModel
                        )
                    }
                }
            }
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun TopAppBarClinicianDashboard(userID: String?) {
        CenterAlignedTopAppBar(
            colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                containerColor = CustomBrown,
                titleContentColor = Color.White
            ),
            title = {
                Text(
                    "Clinician Dashboard",
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    fontWeight = FontWeight.Bold
                )
            },
            navigationIcon = {
                IconButton(onClick = {
                    val intent = Intent(this@ClinicianDashboard, Settings::class.java)
                    intent.putExtra("user_id", userID)
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK)
                    startActivity(intent)
                    finish()

                }) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Back to Settings",
                        tint = Color.White
                    )
                }
            }
        )
    }

    @SuppressLint("UnusedMaterial3ScaffoldPaddingParameter")
    @Composable
    fun ClinicianDashboardContent(
        context: Context,
        userID: String?,
        averageHeifaMale: Double,
        averageHeifaFemale: Double,
        genAIViewModel: GenAIViewModel = viewModel(factory = GenAIViewModelFactory(context.applicationContext as Application))
    ) {
        val application = context.applicationContext as Application
        val insights = genAIViewModel.insights
        val uiState by genAIViewModel.uiState.collectAsState()

        var showDeleteDialog by remember { mutableStateOf(false) }
        var insightToDeleteIndex by remember { mutableIntStateOf(-1) }


        val foodIntakeViewModel: FoodIntakeViewModel = viewModel(
            factory = FoodIntakeViewModel.FoodIntakeViewModelFactory(application)
        )

        val foodIntakes by foodIntakeViewModel.allIntakes.collectAsState(initial = emptyList())

        val prompt =
            "Please do a data analysis / pattern finding based on ALL the patients using all " +
                    "their scores and find patterns. " +
                    "Refer to the following examples for the kind of output to produce, focusing on the content and style: " +
                    "1. Potential Gender Difference in HEIFA Scoring: The data includes columns for both HEIFAtotalscoreMale and HEIFAtotalscoreFemale for each user. In several cases, the potential score calculated for females is slightly higher than that calculated for males, suggesting the HEIFA criteria might result in slightly different potential maximums or scoring based on gender recommendations, independent of the actual user's intake." +
                    "\n2. Low Wholegrain Consumption: The intake of wholegrains appears generally low across this group. Only one user in the provided sample data had a recorded intake and score for wholegrains, while the rest had zero." +
                    "\n3. Variable Water Intake: Consumption of water varies greatly among the users in this dataset, with scores ranging from 0 to 100. There isn't a clear, immediate correlation in this small sample between water intake score and the overall HEIFA score, though some high scorers did have high water intake." +
                    "\n4. Users with high vegetable scores also scored high in fruit" +
                    "\n5. Females showed greater dietary variety" +
                    "\n\nPlease return a string \"Title || Content\", where Title does not have brackets and Content follows the style of the examples."

        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = { TopAppBarClinicianDashboard(userID) },
            bottomBar = { MyBottomBarClinicianDashboard(context, userID, "Settings") }
        ) { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp)
                    .verticalScroll(rememberScrollState())
            ) {

                Spacer(modifier = Modifier.height(20.dp))

                Column(
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "Average HEIFA Score",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Card(
                            modifier = Modifier.weight(1f),
                            elevation = CardDefaults.cardElevation(4.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text(
                                    text = "Male",
                                    style = MaterialTheme.typography.titleMedium
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = "%.2f".format(averageHeifaMale),
                                    style = MaterialTheme.typography.bodyLarge
                                )
                            }
                        }

                        Spacer(modifier = Modifier.width(16.dp))

                        Card(
                            modifier = Modifier.weight(1f),
                            elevation = CardDefaults.cardElevation(4.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text(
                                    text = "Female",
                                    style = MaterialTheme.typography.titleMedium
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = "%.2f".format(averageHeifaFemale),
                                    style = MaterialTheme.typography.bodyLarge
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))
                HorizontalDivider(
                    modifier = Modifier.fillMaxWidth(),
                    thickness = 1.dp,
                    color = Color.Gray
                )
                Spacer(modifier = Modifier.height(24.dp))

                Text(
                    text = "Pattern of Data (Using AI)",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(bottom = 8.dp)
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center
                ) {
                    Button(
                        onClick = { genAIViewModel.generateInsights(prompt,foodIntakes) },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(text = "🚀 Find patterns!")
                    }

                    Spacer(modifier = Modifier.width(16.dp))

                    Button(
                        onClick = { genAIViewModel.clearInsights() },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(text = "🗑️ Delete All")
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                when (uiState) {
                    is UiState.Loading -> {
                        CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
                    }

                    is UiState.Error -> {
                        Text(
                            text = (uiState as UiState.Error).errorMessage,
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.align(Alignment.CenterHorizontally)
                        )
                    }

                    is UiState.Success -> {}

                    else -> {}
                }

                Spacer(modifier = Modifier.height(16.dp))

                Column(
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    insights.forEachIndexed { index, (title, content) ->
                        DataInsightCard(
                            title = title,
                            content = content,
                            onDeleteClick = {
                                showDeleteDialog = true
                                insightToDeleteIndex = index
                            }
                        )
                    }
                }

                if (showDeleteDialog) {
                    AlertDialog(
                        onDismissRequest = { showDeleteDialog = false },
                        title = { Text("Confirm Deletion") },
                        text = { Text("Are you sure you want to delete this insight?") },
                        confirmButton = {
                            TextButton(onClick = {
                                genAIViewModel.deleteInsightAt(insightToDeleteIndex)
                                showDeleteDialog = false
                            }) {
                                Text("Delete")
                            }
                        },
                        dismissButton = {
                            TextButton(onClick = { showDeleteDialog = false }) {
                                Text("Cancel")
                            }
                        }
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}


@Composable
fun MyBottomBarClinicianDashboard(context: Context, userID: String?, currentScreen: String) {
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
                    val isActive = currentScreen == "Home"
                    IconButton(
                        onClick = {
                            if (!isActive) {
                                val intent = Intent(context, HomeScreen::class.java)
                                intent.putExtra("user_id", userID)
                                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                context.startActivity(intent)
                            }
                        },
                        enabled = !isActive
                    ) {
                        Icon(
                            Icons.Filled.Home, contentDescription = "Go Home",
                            tint = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                        )
                    }
                    Text(
                        "Home",
                        fontSize = 11.sp,
                        color = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                    )
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    val isActive = currentScreen == "Insights"
                    IconButton(
                        onClick = {
                            if (!isActive) {
                                val intent = Intent(context, Insights::class.java)
                                intent.putExtra("user_id", userID)
                                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                context.startActivity(intent)
                            }
                        },
                        enabled = !isActive
                    ) {
                        Icon(
                            Icons.Filled.Favorite, contentDescription = "Insights",
                            tint = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                        )
                    }
                    Text(
                        "Insights",
                        fontSize = 11.sp,
                        color = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                    )
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    val isActive = currentScreen == "NutriCoach"
                    IconButton(
                        onClick = {
                            if (!isActive) {
                                val intent = Intent(context, NutriCoach::class.java)
                                intent.putExtra("user_id", userID)
                                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                context.startActivity(intent)
                            }
                        },
                        enabled = !isActive
                    ) {
                        Icon(
                            Icons.Filled.Face, contentDescription = "NutriCoach",
                            tint = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                        )
                    }
                    Text(
                        "NutriCoach",
                        fontSize = 11.sp,
                        color = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                    )
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    val isActive = currentScreen == "Settings"
                    IconButton(
                        onClick = {
                            if (!isActive) {
                                val intent = Intent(context, Settings::class.java)
                                intent.putExtra("user_id", userID)
                                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                context.startActivity(intent)
                            }
                        },
                        enabled = !isActive
                    ) {
                        Icon(
                            Icons.Filled.Settings, contentDescription = "Settings",
                            tint = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                        )
                    }
                    Text(
                        "Settings",
                        fontSize = 11.sp,
                        color = if (isActive) CustomBrown else MaterialTheme.colorScheme.onSurface
                    )
                }
            }
        }
    )
}

@Composable
fun DataInsightCard(
    title: String,
    content: String,
    onDeleteClick: () -> Unit
) {
    var expanded by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f)
                )
                IconButton(onClick = onDeleteClick) {
                    Icon(
                        imageVector = Icons.Default.Delete,
                        contentDescription = "Delete Insight"
                    )
                }
                IconButton(onClick = { expanded = !expanded }) {
                    Icon(
                        imageVector = if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = if (expanded) "Collapse Insight" else "Expand Insight"
                    )
                }
            }
            if (expanded) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(text = content)
            }
        }
    }
}