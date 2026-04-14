import React, { useEffect, useMemo, useState } from 'react';
import { Button, SafeAreaView, ScrollView, Text, TextInput, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as tf from '@tensorflow/tfjs';

const API_BASE = 'https://api.hosturserver.com';
const WS_URL = 'wss://api.hosturserver.com/ws/trading';

type Signal = { symbol: string; confidence: number; action: 'BUY' | 'SELL' | 'HOLD' };

type OfflineDecision = { note: string; timestamp: number };

export default function App() {
  const [symbol, setSymbol] = useState('BTC-USD');
  const [signal, setSignal] = useState<Signal | null>(null);
  const [status, setStatus] = useState('idle');
  const [offlineQueue, setOfflineQueue] = useState<OfflineDecision[]>([]);

  useEffect(() => {
    tf.ready().then(() => setStatus('tf_ready'));
  }, []);

  useEffect(() => {
    const socket = new WebSocket(WS_URL);
    socket.onmessage = (evt) => {
      try {
        const parsed = JSON.parse(evt.data as string) as Signal;
        setSignal(parsed);
      } catch {
        setStatus('ws_parse_error');
      }
    };
    socket.onerror = () => setStatus('ws_error');
    return () => socket.close();
  }, []);

  useEffect(() => {
    AsyncStorage.getItem('offline-decisions').then((raw) => {
      if (!raw) return;
      setOfflineQueue(JSON.parse(raw));
    });
  }, []);

  async function runPrediction() {
    setStatus('predicting');

    const x = tf.tensor2d([[Math.random(), Math.random(), Math.random(), Math.random()]], [1, 4]);
    const model = tf.sequential();
    model.add(tf.layers.dense({ units: 8, activation: 'relu', inputShape: [4] }));
    model.add(tf.layers.dense({ units: 3, activation: 'softmax' }));
    const y = model.predict(x) as tf.Tensor;
    const vals = Array.from(await y.data());

    const top = vals.indexOf(Math.max(...vals));
    const action = top === 0 ? 'BUY' : top === 1 ? 'SELL' : 'HOLD';

    const localSignal: Signal = {
      symbol,
      confidence: Number(Math.max(...vals).toFixed(3)),
      action
    };

    setSignal(localSignal);
    setStatus('predicted');

    await fetch(`${API_BASE}/api/apps/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appSlug: 'autonomous-trading-coach', features: vals, scenario: 'live_prediction' })
    });
  }

  async function saveOfflineDecision() {
    const next = [...offlineQueue, { note: `${symbol}:${signal?.action ?? 'HOLD'}`, timestamp: Date.now() }];
    setOfflineQueue(next);
    await AsyncStorage.setItem('offline-decisions', JSON.stringify(next));
    setStatus('saved_offline');
  }

  const rewardProjection = useMemo(() => {
    const base = 12000;
    const months = 6;
    const compound = base * Math.pow(1.05, months);
    return Math.round(compound);
  }, []);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#0B1220' }}>
      <ScrollView contentContainerStyle={{ padding: 18, gap: 12 }}>
        <Text style={{ color: '#F9FAFB', fontSize: 26, fontWeight: '700' }}>Autonomous Trading Coach</Text>
        <Text style={{ color: '#93C5FD' }}>Realtime + Offline + Predictive AI edge stack</Text>

        <TextInput
          value={symbol}
          onChangeText={setSymbol}
          style={{ backgroundColor: '#111827', color: '#F9FAFB', padding: 12, borderRadius: 12 }}
        />

        <Button title="Run Predictive Model" onPress={runPrediction} />
        <Button title="Save Offline Decision" onPress={saveOfflineDecision} />

        <View style={{ backgroundColor: '#111827', borderRadius: 12, padding: 12 }}>
          <Text style={{ color: '#D1D5DB' }}>Status: {status}</Text>
          <Text style={{ color: '#D1D5DB' }}>Signal: {signal ? `${signal.action} (${signal.confidence})` : 'none'}</Text>
          <Text style={{ color: '#D1D5DB' }}>Projected 6M rewards @5% monthly: £{rewardProjection / 100}</Text>
          <Text style={{ color: '#D1D5DB' }}>Offline decisions queued: {offlineQueue.length}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
