<?php
	// TimesUp PHP server

	// Check if new game session and initialization
	session_start();
    if ((isset($_GET['sid'])) && ($_GET['sid'] != session_id())) {
        session_destroy();
        session_id($_GET['sid']);
        session_start();
		$_SESSION['words'] = [];
		$_SESSION['players'] = [];
		$_SESSION['tStart'] = 0;
		$_SESSION['round'] = 0;
		$_SESSION['step'] = 0;
		$_SESSION['word'] = 0;
		$_SESSION['player'] = 0;
    }

	// Server settings
	define('MAX_PLAYERS_ALLOWED', 20);
	define('MAX_WORDS_PER_PLAYER_ALLOWED', 20);
	define('MAX_CHARS_PER_WORD_ALLOWED', 30);
	define('ROUNDS', 4);

	// Client posted to server
	if ($_SERVER['REQUEST_METHOD'] === 'POST') {
		if (isset($_POST['NewPlayer'])) {
			addPlayer($_POST['NewPlayer']);
		}
		if (isset($_POST['NewWord'])) {
			addWord($_POST['NewWord']);
		}
		if (isset($_POST['TimerStart'])) {
			setTimerStarted();
		}
		if (isset($_POST['TimerStop'])) {
			setTimerStopped();
		}
		if (isset($_POST['AdvanceStep'])) {
			advanceStep();
		}
	}

	addPlayer('Player');
	addWord('Word');

	// Create JSON object
	$gameObj = (object)[];
	$gameObj->players = $_SESSION['players'];
	$gameObj->words = $_SESSION['words'];
	$gameObj->round = $_SESSION['round'];
	$gameObj->step = $_SESSION['step'];
	$gameObj->word = $_SESSION['word'];
	$gameObj->tStart = $_SESSION['tStart'];
	echo json_encode($gameObj);

	// Save UNIX timestamp of timer start
	function setTimerStarted(){
		$_SESSION['tStart'] = time();
	}

	// Reset timer
	function setTimerStopped(){
		$_SESSION['tStart'] = 0;
	}

	// Advance game steps and rounds
	function advanceStep(){
		// Shuffle words on first step
		if ($_SESSION['step'] == 0) { shuffle($_SESSION['words']); }
        $_SESSION['step'] += 1;
        if ($_SESSION['step'] > 4) { # Card tucked away, times up!
            $_SESSION['step'] = 1;
            $_SESSION['player'] += 1;
            $_SESSION['word'] += 1;
		}
        if ($_SESSION['player'] > count($_SESSION['players'])) { $_SESSION['player'] = 1; }
        if ($_SESSION['word'] > count($_SESSION['word'])) { 
            $_SESSION['word'] = 1;
            $_SESSION['round'] += 1;
            shuffle($_SESSION['words']);
		}
        if ($_SESSION['round'] > ROUNDS) { session_destroy(); } // Destroy session for good measure
	}

	// Add a new word to array
	function addWord($str){
		// Server flooding protection
		if (count($_SESSION['words']) < (MAX_WORDS_PER_PLAYER_ALLOWED * MAX_PLAYERS_ALLOWED)) {
			$sanitizedStr = filter_var($str, FILTER_SANITIZE_STRING);
			if (strlen($sanitizedStr) < MAX_CHARS_PER_WORD_ALLOWED) {
				$_SESSION['words'][] = $sanitizedStr;
			}
		}
	}

	// Add Player name to array
	function addPlayer($str){
		// Server flooding protection
		if (count($_SESSION['players']) < MAX_PLAYERS_ALLOWED) {
			$_SESSION['players'][] = filter_var($str, FILTER_SANITIZE_STRING);
		}
	}
	
?>