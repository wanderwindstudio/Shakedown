Shader "Shakedown/Spike/Sharp stars"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Background" }
        Pass
        {
            ZWrite Off
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct Input { float4 position:POSITION; half4 colour:COLOR; };
            struct Varying { float4 position:SV_POSITION; half4 colour:COLOR; };
            Varying Vert(Input v) { Varying o; o.position=TransformObjectToHClip(v.position.xyz); o.colour=v.colour; return o; }
            half4 Frag(Varying i):SV_Target { return half4(i.colour.rgb,1); }
            ENDHLSL
        }
    }
}
