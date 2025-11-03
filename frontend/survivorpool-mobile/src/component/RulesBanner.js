import React, { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { styles } from './styles/RulesBanner.styles';

const RulesBanner = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>How to Play</Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => setIsExpanded(!isExpanded)}
        >
          <Text style={styles.buttonText}>
            {isExpanded ? 'Hide' : 'Show'} Rules
          </Text>
        </TouchableOpacity>
      </View>

      {isExpanded && (
        <View style={styles.rulesContainer}>
          <View style={styles.ruleItem}>
            <Text style={styles.bulletPoint}>"</Text>
            <Text style={styles.ruleText}>
              Pick one team per week that you think will win or draw.
            </Text>
          </View>

          <View style={styles.ruleItem}>
            <Text style={styles.bulletPoint}>"</Text>
            <Text style={styles.ruleText}>
              If your team wins or draws, you advance to the next week.
            </Text>
          </View>

          <View style={styles.ruleItem}>
            <Text style={styles.bulletPoint}>"</Text>
            <Text style={styles.ruleText}>
              If your team loses, you lose one life (you have 3 lives total).
            </Text>
          </View>

          <View style={styles.ruleItem}>
            <Text style={styles.bulletPoint}>"</Text>
            <Text style={styles.ruleText}>
              You can only pick each team twice per season.
            </Text>
          </View>

          <View style={styles.ruleItem}>
            <Text style={styles.bulletPoint}>"</Text>
            <Text style={styles.ruleText}>
              The last player standing wins the pool!
            </Text>
          </View>
        </View>
      )}
    </View>
  );
};

export default RulesBanner;
