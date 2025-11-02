package net.codingivan.foodexport;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.screen.ingame.GenericContainerScreen;
import net.minecraft.item.ItemStack;
import net.minecraft.text.Text;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.Gson;

public class FoodexportClient implements ClientModInitializer {

    private boolean wasChestOpen = false;
    private GenericContainerScreen lastChestScreen = null;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (client == null || client.player == null) return;

            Screen current = client.currentScreen;

            // Detect when a chest is open
            if (current instanceof GenericContainerScreen containerScreen) {
                wasChestOpen = true;
                lastChestScreen = containerScreen;
            }
            // Detect when chest closes (previous tick had chest, now null)
            else if (wasChestOpen && current == null) {
                if (lastChestScreen != null) {
                    exportChestContents(client, lastChestScreen);
                }
                wasChestOpen = false;
                lastChestScreen = null;
            }
        });
    }

    private void exportChestContents(MinecraftClient client, GenericContainerScreen chestScreen) {
        var handler = chestScreen.getScreenHandler();
        var slots = handler.slots;

        // The chest inventory is always the *first* part of slots before player inventory
        // For single chests: 27 slots (3x9)
        // For double chests: 54 slots (6x9)
        int containerSize = handler.getRows() * 9; // works for any chest size

        // --- Collect item names ---
        List<String> itemNames = new ArrayList<>();

        for (int i = 0; i < containerSize; i++) {
            ItemStack stack = slots.get(i).getStack();
            if (!stack.isEmpty()) {
                itemNames.add(stack.getName().getString());
            }
        }

        // --- Prepare JSON payload ---
        var payload = new java.util.HashMap<String, Object>();
        payload.put("player", client.player.getName().getString());
        payload.put("items", itemNames);

        String json = new Gson().toJson(payload);

        // --- Send API POST request asynchronously ---
        new Thread(() -> {
            try {
                HttpClient httpClient = HttpClient.newHttpClient();
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create("http://localhost:5000/api/chest"))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(json))
                        .build();

                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

                System.out.println("POST response code: " + response.statusCode());
                System.out.println("Response body: " + response.body());

            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();


    }
}
