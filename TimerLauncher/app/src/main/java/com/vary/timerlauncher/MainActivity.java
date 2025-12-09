package com.vary.timerlauncher;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.provider.AlarmClock;

import java.util.Objects;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Intent intent = getIntent();
        Uri uri = intent.getData();
        if (uri != null && Objects.equals(uri.getScheme(), "launchtimer")) {
            Integer secs = parseInt(uri.getQueryParameter("seconds"));
            String title = uri.getQueryParameter("title");

            if (secs != null && title != null) {
                launchTimer(secs, title);
            }

            closeSelf();
        }
    }

    private static Integer parseInt(String s) {
        if (s == null) {
            return null;
        }

        try {
            return Integer.parseInt(s);
        }
        catch (NumberFormatException e) {
            e.printStackTrace();
            return null;
        }
    }

    private void launchTimer(int secs, String title) {
        Intent launch = new Intent(AlarmClock.ACTION_SET_TIMER)
                .putExtra(AlarmClock.EXTRA_MESSAGE, title)
                .putExtra(AlarmClock.EXTRA_LENGTH, secs)
                .putExtra(AlarmClock.EXTRA_SKIP_UI, false);

        if (launch.resolveActivity(getApplicationContext().getPackageManager()) != null) {
            launch.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getApplicationContext().startActivity(launch);
        }
    }

    private void closeSelf() {
        // Post the Runnable with a delay
        new Handler().postDelayed(() -> {
            MainActivity.this.finishAndRemoveTask();
            System.exit(0);
        }, 1);
    }
}