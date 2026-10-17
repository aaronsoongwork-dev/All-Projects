package com.fit2081.aaron_34076832.nutritrack.screens

import com.fit2081.aaron_34076832.nutritrack.network.FruitViewModel
import android.annotation.SuppressLint
import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowLeft
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips.MotivationalUiState
import com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips.NutriCoachTips
import com.fit2081.aaron_34076832.nutritrack.network.Fruit
import com.fit2081.aaron_34076832.nutritrack.network.Nutritions
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import androidx.compose.ui.draw.clip
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.data.nutricoach.NutriCoachViewModel


class NutriCoach : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val userId = intent.getStringExtra("user_id") ?: "Unknown ID"

        enableEdgeToEdge()
        setContent {
            A1HealthAppTheme {
                val fruitViewModel: FruitViewModel = viewModel()
                val nutriCoachViewModel: NutriCoachViewModel = viewModel(
                    factory = NutriCoachViewModel.NutriCoachViewModelFactory(application)
                )

                val context = LocalContext.current

                val userPreferencesManager = remember { UserPreferencesManager(context.applicationContext) }
                LaunchedEffect(Unit) {
                    userPreferencesManager.setLastScreenRoute("nutricoach")
                }

                // Set the current user ID for the ViewModel as soon as it's available
                LaunchedEffect(userId) {
                    nutriCoachViewModel.setCurrentUserId(userId)
                }

                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    FruitScreen(
                        userID = userId,
                        context = context,
                        modifier = Modifier.padding(innerPadding),
                        fruitViewModel = fruitViewModel,
                        nutriCoachViewModel = nutriCoachViewModel
                    )
                }
            }
        }
    }

    @SuppressLint("UnusedMaterial3ScaffoldPaddingParameter")
    @Composable
    fun FruitScreen(
        userID: String,
        context: Context,
        modifier: Modifier = Modifier,
        fruitViewModel: FruitViewModel,
        nutriCoachViewModel: NutriCoachViewModel,
    ) {
        val fruitState by fruitViewModel.fruit.collectAsState()
        val allTips by nutriCoachViewModel.allTips.collectAsState(initial = emptyList())
        val motivationalUiState by nutriCoachViewModel.motivationalUiState.collectAsState()

        LaunchedEffect(userID) {
            // Set the patient ID for food intake logic, which also sets the currentUserId for tips
            nutriCoachViewModel.setPatientIdForFoodIntake(userID)
        }

        val isFruitScoreOptimal by nutriCoachViewModel.isFruitScoreOptimal.observeAsState(false)


        val showDeleteTipDialog by nutriCoachViewModel.showDeleteTipDialog.observeAsState(false)
        val tipToDeleteId by nutriCoachViewModel.tipToDeleteId.observeAsState(-1L)
        val showDeleteAllTipsDialog by nutriCoachViewModel.showDeleteAllTipsDialog.observeAsState(false)
        val showAllTipsModal by nutriCoachViewModel.showAllTipsModal.observeAsState(false)

        val showMotivationPromptDialog by nutriCoachViewModel.showMotivationPromptDialog.observeAsState(false)
        val showMotivationQuestion1Dialog by nutriCoachViewModel.showMotivationQuestion1Dialog.observeAsState(false)
        val showMotivationQuestion2Dialog by nutriCoachViewModel.showMotivationQuestion2Dialog.observeAsState(false)
        val showMotivationQuestion3Dialog by nutriCoachViewModel.showMotivationQuestion3Dialog.observeAsState(false)

        val selectedMotivationType by nutriCoachViewModel.selectedMotivationType.observeAsState("")
        val energyLevel by nutriCoachViewModel.energyLevel.observeAsState(3f)
        val additionalNotes by nutriCoachViewModel.additionalNotes.observeAsState("")

        val motivationOptions = listOf("working out", "sleep", "diet", "wellbeing")

        // Ensure pagerState updates when allTips changes
        val pagerState = rememberPagerState(initialPage = 0, pageCount = { allTips.size })
        val coroutineScope = rememberCoroutineScope()


        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = { TopAppBarClinicianDashboard(userID) },
            bottomBar = { MyBottomBarClinicianDashboard(context, userID, "NutriCoach") }
        ) { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp)
                    .verticalScroll(rememberScrollState())
            ) {
                if (!isFruitScoreOptimal) {
                    OptimalFruitDisplay()
                } else {
                    fruitState?.let { fruit ->
                        FruitInfoCard(fruit, fruitViewModel)
                    } ?: run {
                        FruitInfoCard(
                            Fruit(
                                name = "",
                                family = "",
                                genus = "",
                                order = "",
                                nutritions = Nutritions(
                                    calories = 0.0,
                                    fat = 0.0,
                                    sugar = 0.0,
                                    carbohydrates = 0.0,
                                    protein = 0.0
                                )
                            ), fruitViewModel
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                HorizontalDivider(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 2.dp),
                    thickness = 2.dp,
                    color = Color.LightGray
                )
                Spacer(modifier = Modifier.height(16.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Motivational Tips",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                    )
                    TextButton(
                        onClick = { nutriCoachViewModel.setShowAllTipsModal(true) },
                        colors = ButtonDefaults.textButtonColors(contentColor = Color.Gray)
                    ) {
                        Text("View all Tips >>")
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))

                Button(
                    onClick = {
                        nutriCoachViewModel.setShowMotivationPromptDialog(true)
                        nutriCoachViewModel.resetMotivationInputs()
                        nutriCoachViewModel.resetMotivationalUiState()
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Filled.Search, contentDescription = "Generate Motivation")
                    Text("Generate Motivational Tip")
                }

                Spacer(modifier = Modifier.height(16.dp))

                when (motivationalUiState) {
                    is MotivationalUiState.Loading -> {
                        CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
                    }

                    is MotivationalUiState.Error -> {
                        Text(
                            text = (motivationalUiState as MotivationalUiState.Error).errorMessage,
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.align(Alignment.CenterHorizontally)
                        )
                    }
                    else -> { /* Initial or Success states */ }
                }

                Spacer(modifier = Modifier.height(16.dp))

                if (allTips.isEmpty()) {
                    Text("No motivational tips generated yet.")
                } else {
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            IconButton(
                                onClick = {
                                    coroutineScope.launch {
                                        pagerState.animateScrollToPage(pagerState.currentPage - 1)
                                    }
                                },
                                enabled = pagerState.currentPage > 0
                            ) {
                                Icon(
                                    Icons.AutoMirrored.Filled.KeyboardArrowLeft,
                                    contentDescription = "Previous tip",
                                    tint = if (pagerState.currentPage > 0) MaterialTheme.colorScheme.onSurface else Color.LightGray
                                )
                            }

                            Text(
                                text = "${pagerState.currentPage + 1} out of ${allTips.size}",
                                modifier = Modifier.padding(horizontal = 8.dp)
                            )

                            IconButton(
                                onClick = {
                                    coroutineScope.launch {
                                        pagerState.animateScrollToPage(pagerState.currentPage + 1)
                                    }
                                },
                                enabled = pagerState.currentPage < allTips.size - 1
                            ) {
                                Icon(
                                    Icons.AutoMirrored.Filled.KeyboardArrowRight,
                                    contentDescription = "Next tip",
                                    tint = if (pagerState.currentPage < allTips.size - 1) MaterialTheme.colorScheme.onSurface else Color.LightGray
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        HorizontalPager(state = pagerState) { page ->
                            MotivationalTipCard(
                                tip = allTips[page],
                                onDeleteClick = {
                                    nutriCoachViewModel.setShowDeleteTipDialog(true, it.id)
                                }
                            )
                        }
                    }
                }

                if (showDeleteTipDialog) {
                    AlertDialog(
                        onDismissRequest = { nutriCoachViewModel.setShowDeleteTipDialog(false) },
                        title = { Text("Confirm Deletion") },
                        text = { Text("Are you sure you want to delete this motivational tip?") },
                        confirmButton = {
                            Button(onClick = {
                                nutriCoachViewModel.deleteTipById(tipToDeleteId ?: -1L)
                                nutriCoachViewModel.setShowDeleteTipDialog(false)
                            }) {
                                Text("Delete")
                            }
                        },
                        dismissButton = {
                            Button(onClick = { nutriCoachViewModel.setShowDeleteTipDialog(false) }) {
                                Text("Cancel")
                            }
                        }
                    )
                }

                if (allTips.isNotEmpty()) {
                    Button(
                        onClick = { nutriCoachViewModel.setShowDeleteAllTipsDialog(true) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                    ) {
                        Text("Delete All Tips")
                    }
                }

                if (showDeleteAllTipsDialog) {
                    AlertDialog(
                        onDismissRequest = { nutriCoachViewModel.setShowDeleteAllTipsDialog(false) },
                        title = { Text("Confirm Deletion of All Tips") },
                        text = { Text("Are you absolutely sure you want to delete ALL motivational tips for this user? This action cannot be undone.") },
                        confirmButton = {
                            Button(onClick = {
                                nutriCoachViewModel.deleteAllTipsForCurrentUser() // Call the user-specific delete function
                                nutriCoachViewModel.setShowDeleteAllTipsDialog(false)
                            }) {
                                Text("Delete All")
                            }
                        },
                        dismissButton = {
                            Button(onClick = { nutriCoachViewModel.setShowDeleteAllTipsDialog(false) }) {
                                Text("Cancel")
                            }
                        }
                    )
                }
            }

            if (showMotivationPromptDialog) {
                MotivationPromptDialog(
                    onDismiss = { nutriCoachViewModel.setShowMotivationPromptDialog(false) },
                    onYesClick = {
                        nutriCoachViewModel.setShowMotivationPromptDialog(false)
                        nutriCoachViewModel.setShowMotivationQuestion1Dialog(true)
                    },
                    onNoClick = {
                        nutriCoachViewModel.setShowMotivationPromptDialog(false)
                        coroutineScope.launch {
                            nutriCoachViewModel.generateMotivationalMessage(
                                motivationType = "",
                                energyLevel = null,
                                additionalNotes = ""
                            )
                        }
                    }
                )
            }

            if (showMotivationQuestion1Dialog) {
                MotivationQuestion1Dialog(
                    selectedMotivationType = selectedMotivationType,
                    motivationOptions = motivationOptions,
                    onOptionSelected = { onOptionSelected ->
                        nutriCoachViewModel.setSelectedMotivationType(onOptionSelected)
                    },
                    onDismiss = {
                        nutriCoachViewModel.setShowMotivationQuestion1Dialog(false)
                        nutriCoachViewModel.resetMotivationInputs()
                    },
                    onNext = {
                        nutriCoachViewModel.setShowMotivationQuestion1Dialog(false)
                        nutriCoachViewModel.setShowMotivationQuestion2Dialog(true)
                    },
                    onGenerateWithoutMoreInfo = {
                        nutriCoachViewModel.setShowMotivationQuestion1Dialog(false)
                        coroutineScope.launch {
                            nutriCoachViewModel.generateMotivationalMessage(
                                motivationType = selectedMotivationType,
                                energyLevel = null,
                                additionalNotes = ""
                            )
                        }
                    }
                )
            }

            if (showMotivationQuestion2Dialog) {
                MotivationQuestion2Dialog(
                    energyLevel = energyLevel,
                    onEnergyLevelChange = { nutriCoachViewModel.setEnergyLevel(it) },
                    onDismiss = {
                        nutriCoachViewModel.setShowMotivationQuestion2Dialog(false)
                        nutriCoachViewModel.resetMotivationInputs()
                    },
                    onBack = {
                        nutriCoachViewModel.setShowMotivationQuestion2Dialog(false)
                        nutriCoachViewModel.setShowMotivationQuestion1Dialog(true)
                    },
                    onNext = {
                        nutriCoachViewModel.setShowMotivationQuestion2Dialog(false)
                        nutriCoachViewModel.setShowMotivationQuestion3Dialog(true)
                    },
                    onGenerateWithoutMoreInfo = {
                        nutriCoachViewModel.setShowMotivationQuestion2Dialog(false)
                        coroutineScope.launch {
                            nutriCoachViewModel.generateMotivationalMessage(
                                motivationType = selectedMotivationType,
                                energyLevel = energyLevel.toInt(),
                                additionalNotes = ""
                            )
                        }
                    }
                )
            }

            if (showMotivationQuestion3Dialog) {
                MotivationQuestion3Dialog(
                    additionalNotes = additionalNotes,
                    onAdditionalNotesChange = { nutriCoachViewModel.setAdditionalNotes(it) },
                    onDismiss = {
                        nutriCoachViewModel.setShowMotivationQuestion3Dialog(false)
                        nutriCoachViewModel.resetMotivationInputs()
                    },
                    onBack = {
                        nutriCoachViewModel.setShowMotivationQuestion3Dialog(false)
                        nutriCoachViewModel.setShowMotivationQuestion2Dialog(true)
                    },
                    onGenerate = {
                        nutriCoachViewModel.setShowMotivationQuestion3Dialog(false)
                        coroutineScope.launch {
                            nutriCoachViewModel.generateMotivationalMessage(
                                motivationType = selectedMotivationType,
                                energyLevel = energyLevel.toInt(),
                                additionalNotes = additionalNotes
                            )
                        }
                    }
                )
            }

            if (showAllTipsModal) {
                AllTipsModal(
                    allTips = allTips,
                    onDismiss = { nutriCoachViewModel.setShowAllTipsModal(false) },
                    onDeleteClick = { tip ->
                        nutriCoachViewModel.setShowDeleteTipDialog(true, tip.id)
                    }
                )
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
                    "NutriCoach",
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    fontWeight = FontWeight.Bold
                )
            }
        )
    }
}
@Composable
fun FruitInfoCard(fruit: Fruit?, viewModel: FruitViewModel) {
    var fruitNameInput by remember(fruit?.name) { mutableStateOf(fruit?.name ?: "") }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(max = 400.dp)
            .background(Color(0xFFEAF4F4), shape = RoundedCornerShape(8.dp))
            .padding(16.dp)
    ) {
        Text(
            text = "Fruit Info Finder",
            fontWeight = FontWeight.Bold,
            fontSize = 20.sp,
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 8.dp)
        )

        HorizontalDivider(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 1.dp),
            thickness = 2.dp,
            color = Color.LightGray
        )

        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp, bottom = 12.dp)
        ) {
            OutlinedTextField(
                value = fruitNameInput,
                onValueChange = { fruitNameInput = it },
                label = { Text("Fruit Name") },
                placeholder = { Text("e.g. banana") },
                modifier = Modifier.weight(0.75f),
                singleLine = true
            )

            Spacer(modifier = Modifier.width(12.dp))

            Button(
                onClick = {
                    if (fruitNameInput.isNotBlank()) {
                        viewModel.loadFruitDetails(fruitNameInput.lowercase())
                    }
                },
                modifier = Modifier
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF6200EE),
                    contentColor = Color.White
                )
            ) {
                Icon(Icons.Filled.Search, contentDescription = "Details")
                Text("Details")
            }
        }

        if (fruit != null && fruit.name.isNotBlank()) {
            Text(
                text = "Fruit: ${fruit.name}",
                fontWeight = FontWeight.SemiBold,
                fontSize = 16.sp,
                modifier = Modifier.padding(bottom = 8.dp)
            )
        }

        if (fruit != null) {
            NutrientRow(label = "family:", value = fruit.family)
            NutrientRow(label = "calories:", value = fruit.nutritions.calories.toString())
            NutrientRow(label = "fat:", value = fruit.nutritions.fat.toString())
            NutrientRow(label = "sugar:", value = fruit.nutritions.sugar.toString())
            NutrientRow(label = "carbohydrates", value = fruit.nutritions.carbohydrates.toString())
            NutrientRow(label = "protein:", value = fruit.nutritions.protein.toString())
        }
    }
}

@Composable
fun OptimalFruitDisplay() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 200.dp, max = 400.dp)
            .background(Color(0xFFEAF4F4), shape = RoundedCornerShape(8.dp))
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Great job! Your fruit intake is optimal!",
            fontWeight = FontWeight.Bold,
            fontSize = 20.sp,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        Spacer(modifier = Modifier.height(8.dp))
        AsyncImage(
            model = ImageRequest.Builder(LocalContext.current)
                .data("https://picsum.photos/400/250?random=${System.currentTimeMillis()}")
                .crossfade(true)
                .build(),
            contentDescription = "Random image",
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .fillMaxWidth(0.8f)
                .height(150.dp)
                .clip(RoundedCornerShape(8.dp))
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Keep up the excellent work!",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(16.dp))

    }
}

@Composable
fun NutrientRow(label: String, value: String) {
    OutlinedCard(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.outlinedCardColors(
            containerColor = Color.White
        )
    ) {
        Row(
            modifier = Modifier
                .padding(horizontal = 12.dp, vertical = 6.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(text = label, style = MaterialTheme.typography.bodySmall)
            Text(text = value, style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
fun MotivationalTipCard(tip: NutriCoachTips, onDeleteClick: (NutriCoachTips) -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(2.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Generated on: ${
                        SimpleDateFormat(
                            "MMM dd,yyyy HH:mm",
                            Locale.getDefault()
                        ).format(Date(tip.timestamp))
                    }",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.Gray
                )
                IconButton(
                    onClick = { onDeleteClick(tip) },
                    modifier = Modifier
                        .width(24.dp)
                        .height(24.dp)
                ) {
                    Icon(
                        Icons.Filled.Delete,
                        contentDescription = "Delete Tip",
                        tint = MaterialTheme.colorScheme.error
                    )
                }
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = tip.message,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
fun MotivationPromptDialog(
    onDismiss: () -> Unit,
    onYesClick: () -> Unit,
    onNoClick: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Make it Personal") },
        text = { Text("Would you like to provide extra information so we can give you better support?") },
        confirmButton = {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                Button(onClick = onNoClick) {
                    Text("Nope")
                }
                Spacer(Modifier.width(8.dp))

                Button(onClick = onYesClick) {
                    Text("Yes")
                }
            }
        }
    )
}

@Composable
fun MotivationQuestion1Dialog(
    selectedMotivationType: String,
    motivationOptions: List<String>,
    onOptionSelected: (String) -> Unit,
    onDismiss: () -> Unit,
    onNext: () -> Unit,
    onGenerateWithoutMoreInfo: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("What kind of motivation?") },
        text = {
            Column(Modifier.selectableGroup()) {
                motivationOptions.forEach { text ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .height(40.dp)
                            .selectable(
                                selected = (text == selectedMotivationType),
                                onClick = { onOptionSelected(text) },
                                role = Role.RadioButton
                            )
                            .padding(horizontal = 16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = (text == selectedMotivationType),
                            onClick = null
                        )
                        Text(
                            text = text,
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.padding(start = 16.dp)
                        )
                    }
                }
            }
        },
        confirmButton = {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Button(onClick = onGenerateWithoutMoreInfo) {
                        Text("Generate Now")
                    }

                    Spacer(modifier = Modifier.width(8.dp))
                    Button(
                        onClick = onNext,
                        enabled = selectedMotivationType.isNotBlank()
                    ) {
                        Text("Next")
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    Button(onClick = onDismiss) {
                        Text("Cancel")
                    }
                }
            }
        }
    )
}

@Composable
fun MotivationQuestion2Dialog(
    energyLevel: Float,
    onEnergyLevelChange: (Float) -> Unit,
    onDismiss: () -> Unit,
    onBack: () -> Unit,
    onNext: () -> Unit,
    onGenerateWithoutMoreInfo: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("How's your energy lately?") },
        text = {
            Column {
                Slider(
                    value = energyLevel,
                    onValueChange = onEnergyLevelChange,
                    valueRange = 1f..5f,
                    steps = 3,
                    modifier = Modifier.fillMaxWidth()
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("1", style = MaterialTheme.typography.bodySmall)
                    Text(
                        text = "Current: ${energyLevel.toInt()}",
                        modifier = Modifier.weight(1f),
                        textAlign = TextAlign.Center,
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Medium
                    )
                    Text("5", style = MaterialTheme.typography.bodySmall)
                }
            }
        },
        confirmButton = {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Button(onClick = onGenerateWithoutMoreInfo) {
                        Text("Generate Now")
                    }
                    Button(onClick = onNext) {
                        Text("Next")
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Button(onClick = onBack) {
                        Text("Back")
                    }
                    Button(onClick = onDismiss) {
                        Text("Cancel")
                    }
                }
            }
        }
    )
}

@Composable
fun MotivationQuestion3Dialog(
    additionalNotes: String,
    onAdditionalNotesChange: (String) -> Unit,
    onDismiss: () -> Unit,
    onBack: () -> Unit,
    onGenerate: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Anything else? (Optional)") },
        text = {
            OutlinedTextField(
                value = additionalNotes,
                onValueChange = onAdditionalNotesChange,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 100.dp),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text),
                maxLines = 5
            )
        },
        confirmButton = {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    Button(onClick = onGenerate) {
                        Text("Generate Message")
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Button(onClick = onBack) {
                        Text("Back")
                    }
                    Button(onClick = onDismiss) {
                        Text("Cancel")
                    }
                }
            }
        }
    )
}

@Composable
fun AllTipsModal(
    allTips: List<NutriCoachTips>,
    onDismiss: () -> Unit,
    onDeleteClick: (NutriCoachTips) -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("All Motivational Tips") },
        text = {
            if (allTips.isEmpty()) {
                Text("No motivational tips yet.")
            } else {
                LazyColumn {
                    items(allTips) { tip ->
                        MotivationalTipCard(
                            tip = tip,
                            onDeleteClick = onDeleteClick
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                    }
                }
            }
        },
        confirmButton = {
            Button(onClick = onDismiss) {
                Text("Close")
            }
        }
    )
}