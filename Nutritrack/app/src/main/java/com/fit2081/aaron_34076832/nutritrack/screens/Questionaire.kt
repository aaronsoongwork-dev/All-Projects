package com.fit2081.aaron_34076832.nutritrack.screens

import android.annotation.SuppressLint
import android.app.TimePickerDialog
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
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
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.R
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.QuestionnaireRepository
import com.fit2081.aaron_34076832.nutritrack.data.persona.Persona
import com.fit2081.aaron_34076832.nutritrack.ui.questionnaire.QuestionnaireScreenViewModel
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen
import java.util.Calendar

class Questionaire : ComponentActivity() {

    private lateinit var userId: String

    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        userId = intent.getStringExtra("user_id") ?: "Unknown ID"
        Log.d("Questionnaire", "User ID received: $userId")

        enableEdgeToEdge()
        setContent {
            val context = LocalContext.current
            val userPreferencesManager = remember { UserPreferencesManager(context.applicationContext) }

            val questionnaireRepository = QuestionnaireRepository(application)
            val questionnaireScreenViewModel: QuestionnaireScreenViewModel = viewModel(
                factory = QuestionnaireScreenViewModel.QuestionnaireScreenViewModelFactory(application, questionnaireRepository)
            )

            LaunchedEffect(userId) {
                questionnaireScreenViewModel.setUserId(userId)
            }

            LaunchedEffect(Unit) {
                userPreferencesManager.setLastScreenRoute("questionnaire")
            }

            val saveMealTime by questionnaireScreenViewModel.saveMealTime.observeAsState("")
            val saveSleepTime by questionnaireScreenViewModel.saveSleepTime.observeAsState("")
            val saveWakeTime by questionnaireScreenViewModel.saveWakeTime.observeAsState("")

            val fruits by questionnaireScreenViewModel.fruits.observeAsState(false)
            val vege by questionnaireScreenViewModel.vege.observeAsState(false)
            val grains by questionnaireScreenViewModel.grains.observeAsState(false)
            val redMeat by questionnaireScreenViewModel.redMeat.observeAsState(false)
            val seafood by questionnaireScreenViewModel.seafood.observeAsState(false)
            val poultry by questionnaireScreenViewModel.poultry.observeAsState(false)
            val fish by questionnaireScreenViewModel.fish.observeAsState(false)
            val eggs by questionnaireScreenViewModel.eggs.observeAsState(false)
            val nutsSeeds by questionnaireScreenViewModel.nutsSeeds.observeAsState(false)

            val selectedPersona by questionnaireScreenViewModel.selectedPersona.observeAsState(null)

            val showValidationDialog by questionnaireScreenViewModel.showValidationDialog.observeAsState(false)
            val validationMessage by questionnaireScreenViewModel.validationMessage.observeAsState("")
            val saveSuccess by questionnaireScreenViewModel.saveSuccess.observeAsState(null)

            LaunchedEffect(saveSuccess) {
                when (saveSuccess) {
                    true -> {
                        Toast.makeText(context, "Data has been saved!", Toast.LENGTH_LONG).show()
                        val homeScreenIntent = Intent(context, HomeScreen::class.java)
                        homeScreenIntent.putExtra("user_id", userId)
                        context.startActivity(homeScreenIntent)
                        questionnaireScreenViewModel.resetSaveSuccessState()
                    }
                    false -> {
                        questionnaireScreenViewModel.resetSaveSuccessState()
                    }
                    null -> { }
                }
            }

            val mealTimePickerDialog = timePickerFun(saveMealTime) { time -> questionnaireScreenViewModel.onMealTimeSelected(time) }
            val sleepTimePickerDialog = timePickerFun(saveSleepTime) { time -> questionnaireScreenViewModel.onSleepTimeSelected(time) }
            val wakeTimePickerDialog = timePickerFun(saveWakeTime) { time -> questionnaireScreenViewModel.onWakeTimeSelected(time) }


            Scaffold(modifier = Modifier.fillMaxSize(),
                topBar = { TopAppBar()}) { innerPadding ->
                Column(
                    modifier = Modifier
                        .padding(innerPadding)
                        .fillMaxHeight()
                        .padding(horizontal = 24.dp),
                    verticalArrangement = Arrangement.Center ,
                    horizontalAlignment = Alignment.CenterHorizontally

                ) {

                    Spacer(modifier = Modifier.height(10.dp))

                    Text(
                        text = "Tick all the food categories you can eat",
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Left,
                        fontSize = 18.sp,
                        modifier = Modifier.padding(bottom = 2.dp).fillMaxWidth()
                    )

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            CheckboxWithLabel("Fruits", fruits) { checked -> questionnaireScreenViewModel.toggleFruits(checked) }
                            CheckboxWithLabel("Vegetables", vege) { checked -> questionnaireScreenViewModel.toggleVege(checked) }
                            CheckboxWithLabel("Grains", grains) { checked -> questionnaireScreenViewModel.toggleGrains(checked) }
                        }

                        Column{
                            CheckboxWithLabel("Red Meat", redMeat) { checked -> questionnaireScreenViewModel.toggleRedMeat(checked) }
                            CheckboxWithLabel("Seafood", seafood) { checked -> questionnaireScreenViewModel.toggleSeafood(checked) }
                            CheckboxWithLabel("Poultry", poultry) { checked -> questionnaireScreenViewModel.togglePoultry(checked) }
                        }

                        Column{
                            CheckboxWithLabel("Fish", fish) { checked -> questionnaireScreenViewModel.toggleFish(checked) }
                            CheckboxWithLabel("Eggs", eggs) { checked -> questionnaireScreenViewModel.toggleEggs(checked) }
                            CheckboxWithLabel("Nuts/Seeds", nutsSeeds) { checked -> questionnaireScreenViewModel.toggleNutsSeeds(checked) }
                        }
                    }

                    Spacer(Modifier.height(10.dp))

                    Column(
                        modifier = Modifier.padding(2.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "Your Persona",
                            fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Left,
                            modifier = Modifier.fillMaxWidth(),
                            fontSize = 18.sp,
                        )

                        Spacer(modifier = Modifier.height(2.dp))

                        Text(
                            text = "People can be broadly classified into 6 different" +
                                    " types based" +
                                    " on their eating preferences. Click on each button" +
                                    " below to find " +
                                    "out the different types, and select the type that " +
                                    "best fits you!",
                            fontSize = 14.sp,
                            textAlign = TextAlign.Left,
                            lineHeight = 14.sp,
                        )
                    }

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center,
                        modifier = Modifier.padding(2.dp)
                    ){
                        val persona1ID = R.drawable.persona_1
                        val persona2ID = R.drawable.persona_2
                        val persona3ID = R.drawable.persona_3
                        val persona4ID = R.drawable.persona_4
                        val persona5ID = R.drawable.persona_5
                        val persona6ID = R.drawable.persona_6

                        Column (
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            ShowButtonAndModal(
                                "Health Devotee",
                                "I’m passionate about healthy eating &" +
                                        " health plays a big part in my life. I use social" +
                                        " media to follow active lifestyle " +
                                        "personalities or get new recipes/exercise ideas. I may" +
                                        " even buy superfoods or follow a p" +
                                        "articular type of diet. I like to think I am super " +
                                        "healthy.",
                                persona1ID)

                            ShowButtonAndModal("Balance Seeker",
                                "I try and live a balanced lifestyle, " +
                                        "and I think that all foods are okay in moderation. " +
                                        "I shouldn’t have to feel guilty " +
                                        "about eating a piece of cake now and again. I get " +
                                        "all sorts of inspiration from social " +
                                        "media like finding out about new restaurants, fun " +
                                        "recipes and sometimes " +
                                        "healthy eating tips.",
                                persona4ID)
                        }

                        Spacer(modifier = Modifier.width(16.dp))

                        Column (
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ){
                            ShowButtonAndModal(
                                "Mindful Eater",
                                "I’m health-conscious and being healthy and eating healthy" +
                                        " is important to me. " +
                                        "Although health means different things to different " +
                                        "people, I make conscious " +
                                        "lifestyle decisions about eating based on what I " +
                                        "believe healthy means. I look for new " +
                                        "recipes and healthy eating information on social media.",
                                persona2ID)

                            ShowButtonAndModal("Health Procrastinator",
                                "I’m contemplating healthy eating " +
                                        "but it’s not a priority for me right now. I " +
                                        "know the basics about what it means to be " +
                                        "healthy, but it doesn’t seem relevant to me " +
                                        "right now. I have taken a few steps to be " +
                                        "healthier but I am not motivated to make it " +
                                        "a high priority because I have too many other " +
                                        "things going on in my life.",
                                persona5ID)
                        }

                        Spacer(modifier = Modifier.width(16.dp))

                        Column (
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            ShowButtonAndModal("Wellness Striver",
                                "I aspire to be healthy (but struggle sometimes). " +
                                        "Healthy eating is hard work! I’ve tried to improve " +
                                        "my diet, but always find things that make it " +
                                        "difficult to stick with the changes. Sometimes I " +
                                        "notice recipe ideas or healthy eating hacks, " +
                                        "and if it’s easy enough, I’ll give it a go.",
                                persona3ID)

                            ShowButtonAndModal("Food Carefree",
                                "I’m not bothered about healthy eating. I don’t" +
                                        " really see the point and I don’t think about it. I " +
                                        "don’t really notice healthy eating tips" +
                                        " or recipes and I don’t care what I eat.",
                                persona6ID)
                        }
                    }

                    Spacer(Modifier.height(10.dp))

                    var expanded by remember { mutableStateOf(false) }
                    val optionsForPersona = Persona.entries

                    Text(
                        text = "Which persona fits you best?",
                        modifier = Modifier.fillMaxWidth(),
                        textAlign = TextAlign.Left,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(Modifier.height(10.dp))

                    ExposedDropdownMenuBox(
                        expanded = expanded,
                        onExpandedChange = { expanded = true }
                    ) {
                        OutlinedTextField(
                            value = selectedPersona?.name?.replace("_", " ") ?: "Please Select Option",
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Please Select Option",
                                fontWeight = FontWeight.Bold) },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(
                                expanded = expanded) },
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier
                                .menuAnchor()
                                .fillMaxWidth()
                                .height(56.dp)
                        )

                        ExposedDropdownMenu(
                            expanded = expanded,
                            onDismissRequest = { expanded = false }
                        ) {
                            optionsForPersona.forEach { chosenPersona ->
                                DropdownMenuItem(
                                    text = { Text(chosenPersona.name.replace("_", " ")) },
                                    onClick = {
                                        questionnaireScreenViewModel.onPersonaSelected(chosenPersona)
                                        expanded = false
                                    }
                                )
                            }
                        }
                    }

                    Spacer(Modifier.height(20.dp))

                    Text(
                        text = "Timings",
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Left,
                        modifier = Modifier.padding(4.dp).fillMaxWidth(),
                        fontSize = 20.sp,
                    )

                    Column (
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ){
                        Row(
                            modifier = Modifier.padding(4.dp).fillMaxWidth()
                        ) {
                            Text(
                                "What time of day approx. do you\n" +
                                        "normally eat your biggest meal?",
                                textAlign = TextAlign.Left,
                                fontSize = 14.sp
                            )

                            Spacer(Modifier.width(40.dp))

                            Button(onClick = { mealTimePickerDialog.show()
                            },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = CustomGreen)
                            ) {
                                Text(
                                    text = saveMealTime.ifBlank { "Time" }
                                )
                            }
                        }

                        Row(
                            modifier = Modifier.padding(4.dp).fillMaxWidth())
                        {
                            Text(
                                "What time of day approx. do you\n" +
                                        "go to sleep at night?",
                                textAlign = TextAlign.Left,
                                fontSize = 14.sp
                            )

                            Spacer(Modifier.width(40.dp))

                            Button(onClick = { sleepTimePickerDialog.show() },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = CustomGreen)
                            ) {
                                Text(
                                    text = saveSleepTime.ifBlank { "Time" }
                                )
                            }
                        }

                        Row(
                            modifier = Modifier.padding(4.dp).fillMaxWidth()
                        ) {
                            Text(
                                "What time of day approx. do you\n" +
                                        "normally wake up?",
                                textAlign = TextAlign.Left,
                                fontSize = 14.sp
                            )

                            Spacer(Modifier.width(40.dp))

                            Button(onClick = { wakeTimePickerDialog.show() },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = CustomGreen)
                            ) {
                                Text(
                                    text = saveWakeTime.ifBlank { "Time" }
                                )
                            }
                        }
                    }

                    Spacer(Modifier.height(20.dp))

                    Button(
                        onClick = { questionnaireScreenViewModel.saveQuestionnaire() },
                        colors = ButtonDefaults.buttonColors(containerColor = CustomBrown)
                    ) {
                        Text(text = "🔒 Save")
                    }

                    if (showValidationDialog) {
                        AlertDialog(
                            onDismissRequest = { questionnaireScreenViewModel.dismissValidationDialog() },
                            title = { Text("Validation Error") },
                            text = { Text(validationMessage) },
                            confirmButton = {
                                Button(onClick = { questionnaireScreenViewModel.dismissValidationDialog() }) {
                                    Text("Understood")
                                }
                            }
                        )
                    }
                }
            }
        }
    }

    @Composable
    fun ShowButtonAndModal(stringNameModal: String, stringText: String, intImageResId: Int) {
        var showDialog by remember { mutableStateOf(false) }

        Button(
            onClick = { showDialog = true },
            colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 0.dp),
            shape = RoundedCornerShape(6.dp)
        ) {
            Text(
                text = stringNameModal,
                fontSize = 11.sp,
            )
        }

        if (showDialog) {
            AlertDialog(
                onDismissRequest = { showDialog = false },
                title = { Text(stringNameModal, fontWeight = FontWeight.Bold, fontSize = 20.sp) },
                text = {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Image(
                            painter = painterResource(id = intImageResId),
                            contentDescription = stringNameModal,
                            modifier = Modifier.size(140.dp)
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        Text(
                            text = stringText,
                            fontSize = 14.sp,
                            lineHeight = 20.sp,
                            textAlign = TextAlign.Center
                        )
                    }
                },
                confirmButton = {
                    Button(onClick = { showDialog = false }) {
                        Text("Close")
                    }
                }
            )
        }
    }

    @SuppressLint("DefaultLocale")
    @Composable
    fun timePickerFun(currentTime: String, onTimeSelected: (String) -> Unit): TimePickerDialog {
        val mContext = LocalContext.current
        val mCalendar = Calendar.getInstance()

        val (initialHour, initialMinute) = if (currentTime.isNotBlank()) {
            try {
                val parts = currentTime.split(":")
                Pair(parts[0].toInt(), parts[1].toInt())
            } catch (e: Exception) {
                Log.e("TimePicker", "Error parsing time: $currentTime", e)
                Pair(mCalendar.get(Calendar.HOUR_OF_DAY), mCalendar.get(Calendar.MINUTE))
            }
        } else {
            Pair(mCalendar.get(Calendar.HOUR_OF_DAY), mCalendar.get(Calendar.MINUTE))
        }

        val timePickerDialog = TimePickerDialog(
            mContext,
            { _, selectedHour: Int, selectedMinute: Int ->
                onTimeSelected(String.format("%02d:%02d", selectedHour, selectedMinute))
            },
            initialHour, initialMinute, false
        )
        return timePickerDialog
    }


    @Composable
    fun CheckboxWithLabel(stringLabel: String, checkedState: Boolean, onCheckedChange: (Boolean) -> Unit) {
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Checkbox(
                checked = checkedState,
                onCheckedChange = onCheckedChange,
                colors = CheckboxDefaults.colors(checkedColor = CustomGreen)
            )
            Text(
                text = stringLabel,
                modifier = Modifier.clickable { onCheckedChange(!checkedState) }
            )
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun TopAppBar() {
        CenterAlignedTopAppBar(
            colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                containerColor = CustomBrown,
                titleContentColor = Color.White
            ),
            title = {
                Text(
                    "Food Intake Questionnaire",
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    fontWeight = FontWeight.Bold
                )
            },
            navigationIcon = {
                IconButton(onClick = {
                    val intent = Intent(this@Questionaire, LogInPage::class.java)
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK)
                    startActivity(intent)
                    finish()
                }) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Back to Login",
                        tint = Color.White
                    )
                }
            }
        )
    }
}